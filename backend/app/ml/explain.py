"""Explainable AI (XAI) and Prediction Explanation Module

Provides global feature importances and local per-prediction contributing factors.
Presents feature contributions as model explanations rather than absolute physical network causality.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


class PredictionExplainer:
    """Generates global and local explanations for network predictions."""

    @staticmethod
    def get_global_feature_importance(model, feature_names: List[str]) -> List[Dict[str, Any]]:
        """Extracts normalized feature importance weights from fitted pipeline classifier."""
        classifier = model.named_steps.get("classifier") if hasattr(model, "named_steps") else model

        importances = None
        if hasattr(classifier, "feature_importances_"):
            importances = classifier.feature_importances_
        elif hasattr(classifier, "coef_"):
            # For linear models, average absolute coefficient across classes
            importances = np.mean(np.abs(classifier.coef_), axis=0)

        if importances is None:
            return []

        # Truncate or match feature names
        num_features = min(len(feature_names), len(importances))
        sorted_pairs = sorted(
            [(feature_names[i], float(importances[i])) for i in range(num_features)],
            key=lambda x: x[1],
            reverse=True
        )

        total_sum = sum(v for _, v in sorted_pairs) or 1.0
        return [
            {
                "feature": name,
                "importance": round(val / total_sum, 4),
                "importance_pct": round((val / total_sum) * 100.0, 2)
            }
            for name, val in sorted_pairs
        ]

    @staticmethod
    def explain_prediction(
        predicted_class: str,
        confidence: float,
        features: Dict[str, Any],
        global_importances: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Synthesizes human-interpretable contributing factors for a single prediction."""
        factors: List[str] = []

        lat = float(features.get("latency", 0.0))
        loss = float(features.get("packet_loss", 0.0))
        jit = float(features.get("jitter", 0.0))
        bw = float(features.get("download_bandwidth", 0.0))
        util = float(features.get("network_utilization", 0.0))
        sig = features.get("signal_strength")

        if predicted_class == "POOR":
            if loss >= 3.0:
                factors.append(f"High packet loss ({loss:.1f}%) impacting packet delivery")
            if lat >= 120.0:
                factors.append(f"Elevated round-trip latency ({lat:.1f} ms) causing transit delay")
            if jit >= 20.0:
                factors.append(f"Severe packet delay variation / jitter ({jit:.1f} ms)")
            if bw <= 5.0:
                factors.append(f"Constrained download throughput ({bw:.2f} Mbps)")
            if util >= 80.0:
                factors.append(f"High interface link utilization ({util:.1f}%) indicating queue congestion")
            if sig is not None and sig < 40.0:
                factors.append(f"Weak wireless signal strength ({sig:.1f}%)")

            if not factors:
                factors.append("Accumulated multi-metric QoS threshold degradation across network parameters")

        elif predicted_class == "MODERATE":
            if 50.0 <= lat < 140.0:
                factors.append(f"Moderate latency ({lat:.1f} ms)")
            if 0.5 <= loss < 4.0:
                factors.append(f"Intermittent packet loss detected ({loss:.1f}%)")
            if 8.0 <= jit < 25.0:
                factors.append(f"Noticeable delay variation ({jit:.1f} ms)")
            if 5.0 <= bw < 25.0:
                factors.append(f"Moderate download throughput ({bw:.2f} Mbps)")
            if 50.0 <= util < 85.0:
                factors.append(f"Moderate interface traffic load ({util:.1f}%)")
            if sig is not None and 35.0 <= sig < 65.0:
                factors.append(f"Sub-optimal Wi-Fi signal level ({sig:.1f}%)")

            if not factors:
                factors.append("Intermediate metrics lying between pristine QoS and critical failure bounds")

        else:  # GOOD
            factors.append(f"Low round-trip latency ({lat:.1f} ms)")
            factors.append(f"Negligible packet loss ({loss:.1f}%)")
            factors.append(f"Stable delay variation / low jitter ({jit:.1f} ms)")
            factors.append(f"Healthy download throughput ({bw:.1f} Mbps)")
            if sig is not None:
                factors.append(f"Strong wireless signal ({sig:.1f}%)")

        return {
            "predicted_class": predicted_class,
            "confidence": round(confidence, 4),
            "confidence_percentage": round(confidence * 100.0, 1),
            "contributing_factors": factors,
            "disclaimer": "Feature contributions reflect statistical model explanations and empirical thresholds, not absolute physical causality."
        }
