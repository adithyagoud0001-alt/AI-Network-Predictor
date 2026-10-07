"""Model Evaluation Module

Computes multiclass classification metrics (Accuracy, Macro Precision, Macro Recall,
Macro F1, Confusion Matrix, Classification Report) across train, validation, and test splits.
"""

from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix
)


def evaluate_multiclass_model(
    model,
    X,
    y_true: List[str],
    classes: List[str]
) -> Dict[str, Any]:
    """Evaluates a fitted pipeline/model on provided data."""
    y_pred = model.predict(X)

    acc = float(accuracy_score(y_true, y_pred))
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )

    report = classification_report(y_true, y_pred, target_names=classes, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=classes)

    return {
        "accuracy": round(acc, 4),
        "macro_precision": round(float(p_macro), 4),
        "macro_recall": round(float(r_macro), 4),
        "macro_f1": round(float(f1_macro), 4),
        "weighted_f1": round(float(f1_weighted), 4),
        "confusion_matrix": cm.tolist(),
        "classes": classes,
        "classification_report": report
    }
