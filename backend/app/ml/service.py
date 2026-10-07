"""Prediction and Inference Service Engine

Loads the trained champion pipeline, processes single or streaming telemetry,
computes stability scores, generates explanations, and evaluates degradation risk.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd

from app.ml.features import (
    StreamingFeatureEngineer,
    ALL_MODEL_FEATURES
)
from app.ml.stability import NetworkStabilityEngine
from app.ml.explain import PredictionExplainer
from app.ml.degradation import NetworkDegradationDetector, DegradationAlert
from app.schemas.network import NetworkTelemetry
from app.schemas.prediction import (
    PredictRequest,
    PredictResponse,
    PredictionExplanation,
    FuturePredictionForecast,
    ModelMetadataResponse
)

logger = logging.getLogger(__name__)


class PredictionEngine:
    """Singleton-style service wrapping ML inference and QoS scoring."""

    def __init__(self, models_dir: Optional[str] = None):
        if models_dir is None:
            models_dir = str(Path(__file__).resolve().parent / "models")
        self.models_dir = Path(models_dir)
        self.pipeline = None
        self.metadata: Dict[str, Any] = {}
        self.streaming_engineer = StreamingFeatureEngineer(window_size=5)
        self.degradation_detector = NetworkDegradationDetector(min_window_samples=3)
        self.load_model()

    def load_model(self) -> None:
        """Loads serialized champion pipeline and metadata."""
        pipe_path = self.models_dir / "champion_pipeline.joblib"
        meta_path = self.models_dir / "model_metadata.json"

        if pipe_path.exists():
            try:
                self.pipeline = joblib.load(pipe_path)
                logger.info(f"Loaded champion pipeline from {pipe_path}")
            except Exception as exc:
                logger.error(f"Failed loading champion pipeline: {exc}")
        else:
            logger.warning(f"No champion pipeline found at {pipe_path}")

        if meta_path.exists():
            try:
                with open(meta_path, "r") as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded model metadata version {self.metadata.get('model_version')}")
            except Exception as exc:
                logger.error(f"Failed loading model metadata: {exc}")

    def get_metadata_response(self) -> ModelMetadataResponse:
        """Returns structured metadata response."""
        return ModelMetadataResponse(
            model_version=self.metadata.get("model_version", "1.0.0"),
            timestamp=self.metadata.get("timestamp", datetime.now(timezone.utc).isoformat()),
            champion_model_name=self.metadata.get("champion_model_name", "Random Forest"),
            classes=self.metadata.get("classes", ["GOOD", "MODERATE", "POOR"]),
            input_features=self.metadata.get("input_features", ALL_MODEL_FEATURES),
            validation_comparison=self.metadata.get("validation_comparison", []),
            champion_test_metrics=self.metadata.get("champion_test_metrics", {}),
            global_feature_importances=self.metadata.get("global_feature_importances", []),
            pipeline_file=self.metadata.get("pipeline_file", "champion_pipeline.joblib")
        )

    def predict_telemetry(
        self,
        telemetry: Dict[str, Any],
        recent_history: Optional[List[NetworkTelemetry]] = None
    ) -> PredictResponse:
        """Runs end-to-end inference for a single telemetry snapshot."""
        # 1. Feature Engineering
        feats = self.streaming_engineer.transform_single(telemetry)
        feats_df = pd.DataFrame([feats])[ALL_MODEL_FEATURES]

        # 2. ML Prediction and Probabilities
        if self.pipeline is not None:
            pred_class = str(self.pipeline.predict(feats_df)[0])
            if hasattr(self.pipeline, "predict_proba"):
                probs = self.pipeline.predict_proba(feats_df)[0]
                classes = list(self.pipeline.classes_)
                prob_dict = {classes[i]: round(float(probs[i]), 4) for i in range(len(classes))}
                conf = float(np.max(probs))
            else:
                prob_dict = {pred_class: 1.0}
                conf = 1.0
        else:
            # Fallback heuristic if model not loaded
            pred_class = "GOOD" if feats["latency"] < 50 and feats["packet_loss"] < 1 else "POOR"
            conf = 0.85
            prob_dict = {"GOOD": 0.5, "MODERATE": 0.3, "POOR": 0.2}

        # 3. Network Stability Score (Logically independent of ML)
        stability_score = NetworkStabilityEngine.calculate_score(
            latency=feats["latency"],
            packet_loss=feats["packet_loss"],
            jitter=feats["jitter"],
            download_bandwidth=feats["download_bandwidth"],
            upload_bandwidth=feats["upload_bandwidth"],
            network_utilization=feats["network_utilization"],
            signal_strength=telemetry.get("signal_strength")
        )
        grade = "EXCELLENT" if stability_score >= 85 else ("STABLE" if stability_score >= 70 else ("DEGRADED" if stability_score >= 45 else "CRITICAL"))

        # 4. Explainable AI (Contributing factors)
        explanation_dict = PredictionExplainer.explain_prediction(
            predicted_class=pred_class,
            confidence=conf,
            features=feats,
            global_importances=self.metadata.get("global_feature_importances")
        )

        explanation = PredictionExplanation(
            predicted_class=pred_class,
            confidence=round(conf, 4),
            confidence_percentage=round(conf * 100.0, 1),
            contributing_factors=explanation_dict["contributing_factors"],
            disclaimer=explanation_dict["disclaimer"]
        )

        # 5. Future Forecasting Extension (Section 13)
        future_forecast = self._project_future_state(feats, pred_class, stability_score)

        return PredictResponse(
            timestamp=datetime.now(timezone.utc),
            predicted_class=pred_class,
            confidence=round(conf, 4),
            confidence_percentage=round(conf * 100.0, 1),
            class_probabilities=prob_dict,
            stability_score=stability_score,
            stability_grade=grade,
            explanation=explanation,
            future_forecast=future_forecast,
            model_version=self.metadata.get("model_version", "1.0.0"),
            model_name=self.metadata.get("champion_model_name", "Random Forest")
        )

    def _project_future_state(
        self,
        features: Dict[str, Any],
        current_state: str,
        current_score: float
    ) -> FuturePredictionForecast:
        """Projects near-term (30s) connection state via trend extrapolation."""
        lat_change = features.get("latency_change_rate", 0.0)
        loss_change = features.get("packet_loss_change_rate", 0.0)

        # Negative trend indicates worsening
        if lat_change > 0.15 or loss_change > 1.0:
            trend = "DEGRADING"
            if current_state == "GOOD":
                forecast_state = "MODERATE"
            else:
                forecast_state = "POOR"
            forecast_conf = 0.78
        elif lat_change < -0.10 and loss_change <= 0.0:
            trend = "IMPROVING"
            forecast_state = "GOOD" if current_state == "MODERATE" else "MODERATE"
            forecast_conf = 0.82
        else:
            trend = "STABLE"
            forecast_state = current_state
            forecast_conf = 0.90

        return FuturePredictionForecast(
            horizon_seconds=30,
            forecasted_state=forecast_state,
            stability_trend=trend,
            forecast_confidence=forecast_conf
        )


prediction_engine = PredictionEngine()
