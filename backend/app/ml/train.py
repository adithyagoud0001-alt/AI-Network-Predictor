"""Model Training and Selection Pipeline

Trains and compares 5 classical & ensemble machine learning models:
1. Logistic Regression
2. Decision Tree
3. Random Forest
4. Gradient Boosting
5. XGBoost

Performs stratified splitting (train/val/test), cross-validation, hyperparameter tuning,
evaluates macro F1 score, selects the champion model, and serializes the complete
end-to-end preprocessing + model pipeline with metadata.
"""

import json
import logging
import time
from datetime import datetime, timezone
import sys
from pathlib import Path
from typing import Dict, Any, List

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

from app.ml.features import FeatureEngineer, ALL_MODEL_FEATURES
from app.ml.preprocessor import build_preprocessor
from app.ml.evaluate import evaluate_multiclass_model
from app.ml.explain import PredictionExplainer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CLASSES = ["GOOD", "MODERATE", "POOR"]


def train_and_evaluate_models(
    dataset_path: str,
    models_dir: str,
    random_state: int = 42
) -> Dict[str, Any]:
    """Loads dataset, engineers features, trains all candidate models, and saves champion pipeline."""
    out_dir = Path(models_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading raw dataset from {dataset_path}...")
    raw_df = pd.read_csv(dataset_path)

    # 1. Feature Engineering
    logger.info("Performing feature engineering (rolling windows, rate-of-change, signal imputation)...")
    df = FeatureEngineer.engineer_batch_dataframe(raw_df)

    # Validate target presence
    target_col = "heuristic_quality_label"
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")

    X = df[ALL_MODEL_FEATURES].copy()
    y = df[target_col].copy()

    # 2. Train / Validation / Test Splitting (70% train, 15% val, 15% test)
    # Stratified to maintain class distributions
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.15, random_state=random_state, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.17647, random_state=random_state, stratify=y_temp  # 0.17647 of 0.85 is ~0.15
    )

    logger.info(f"Split sizes: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")

    # Label encoding for XGBoost compatibility (0, 1, 2)
    le = LabelEncoder()
    le.fit(CLASSES)
    y_train_enc = le.transform(y_train)
    y_val_enc = le.transform(y_val)
    y_test_enc = le.transform(y_test)

    # 3. Define Candidate Models
    candidate_estimators = {
        "Logistic Regression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=random_state
        ),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=10,
            class_weight="balanced",
            random_state=random_state
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=100,
            max_depth=12,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=random_state
        ),
        "XGBoost": XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=random_state,
            eval_metric="mlogloss",
            n_jobs=-1
        )
    }

    comparison_results: List[Dict[str, Any]] = []
    trained_pipelines: Dict[str, Pipeline] = {}

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)

    logger.info("Training and cross-validating candidate models...")

    for name, estimator in candidate_estimators.items():
        start_t = time.time()
        # Build clean pipeline with preprocessor + classifier
        preprocessor = build_preprocessor()
        pipe = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("classifier", estimator)
        ])

        # Train on X_train
        if name == "XGBoost":
            pipe.fit(X_train, y_train_enc)
            # Cross validation
            cv_scores = cross_val_score(pipe, X_train, y_train_enc, cv=cv, scoring="f1_macro", n_jobs=-1)
            # Evaluate on validation set
            val_preds_enc = pipe.predict(X_val)
            val_preds = le.inverse_transform(val_preds_enc)
        else:
            pipe.fit(X_train, y_train)
            cv_scores = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="f1_macro", n_jobs=-1)
            val_preds = pipe.predict(X_val)

        train_duration = time.time() - start_t

        # Validation evaluation
        val_eval = evaluate_multiclass_model(
            model=pipe if name != "XGBoost" else WrappedXGBPipeline(pipe, le),
            X=X_val,
            y_true=y_val.tolist(),
            classes=CLASSES
        )

        model_summary = {
            "model_name": name,
            "train_duration_sec": round(train_duration, 2),
            "cv_macro_f1_mean": round(float(np.mean(cv_scores)), 4),
            "cv_macro_f1_std": round(float(np.std(cv_scores)), 4),
            "val_accuracy": val_eval["accuracy"],
            "val_macro_f1": val_eval["macro_f1"],
            "val_macro_precision": val_eval["macro_precision"],
            "val_macro_recall": val_eval["macro_recall"],
            "val_weighted_f1": val_eval["weighted_f1"]
        }
        comparison_results.append(model_summary)
        trained_pipelines[name] = pipe if name != "XGBoost" else WrappedXGBPipeline(pipe, le)

        logger.info(
            f"Model '{name}': Val Macro F1={model_summary['val_macro_f1']:.4f}, "
            f"Val Acc={model_summary['val_accuracy']:.4f}, CV Macro F1={model_summary['cv_macro_f1_mean']:.4f}"
        )

    # 4. Model Selection based on Validation Macro F1 Score
    # (Never assume Random Forest is best; select champion objectively)
    comparison_results.sort(key=lambda x: x["val_macro_f1"], reverse=True)
    best_summary = comparison_results[0]
    champion_name = best_summary["model_name"]
    champion_pipeline = trained_pipelines[champion_name]

    logger.info(f"==> Selected Champion Model: {champion_name} (Val Macro F1 = {best_summary['val_macro_f1']})")

    # 5. Final Evaluation on Held-Out Test Set (Unbiased)
    test_eval = evaluate_multiclass_model(
        model=champion_pipeline,
        X=X_test,
        y_true=y_test.tolist(),
        classes=CLASSES
    )
    logger.info(f"Champion Test Set Results: Accuracy={test_eval['accuracy']}, Macro F1={test_eval['macro_f1']}")

    # 6. Global Feature Importance Extraction
    global_importances = PredictionExplainer.get_global_feature_importance(
        champion_pipeline, ALL_MODEL_FEATURES
    )

    # 7. Persistence
    pipeline_save_path = out_dir / "champion_pipeline.joblib"
    joblib.dump(champion_pipeline, pipeline_save_path)
    logger.info(f"Serialized complete champion pipeline to: {pipeline_save_path}")

    # Save metadata JSON
    metadata = {
        "model_version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "champion_model_name": champion_name,
        "classes": CLASSES,
        "input_features": ALL_MODEL_FEATURES,
        "validation_comparison": comparison_results,
        "champion_test_metrics": test_eval,
        "global_feature_importances": global_importances,
        "pipeline_file": pipeline_save_path.name
    }

    metadata_path = out_dir / "model_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved model metadata to: {metadata_path}")

    return metadata


class WrappedXGBPipeline:
    """Wrapper around XGBoost pipeline to handle string labels transparently."""

    def __init__(self, pipe: Pipeline, label_encoder: LabelEncoder):
        self.pipe = pipe
        self.le = label_encoder
        self.classes_ = self.le.classes_

    @property
    def named_steps(self):
        return self.pipe.named_steps

    def fit(self, X, y):
        y_enc = self.le.transform(y)
        self.pipe.fit(X, y_enc)
        return self

    def predict(self, X):
        preds_enc = self.pipe.predict(X)
        return self.le.inverse_transform(preds_enc)

    def predict_proba(self, X):
        return self.pipe.predict_proba(X)


if __name__ == "__main__":
    dataset_file = Path(__file__).resolve().parent.parent / "data" / "datasets" / "network_telemetry_dataset.csv"
    models_folder = Path(__file__).resolve().parent / "models"
    train_and_evaluate_models(str(dataset_file), str(models_folder))
