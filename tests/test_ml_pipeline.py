"""Unit tests for ML Inference Pipeline and Prediction Engine."""

import sys
from pathlib import Path
import pytest
import numpy as np

backend_root = Path(__file__).resolve().parent.parent / "backend"
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.ml.service import prediction_engine


def test_champion_model_loaded():
    """Verify champion pipeline is initialized and loaded."""
    assert prediction_engine.pipeline is not None
    assert prediction_engine.metadata is not None
    assert "champion_model_name" in prediction_engine.metadata


def test_prediction_probabilities_sum_to_one():
    """Verify output probabilities are normalized and sum to 1.0."""
    telem = {
        "latency": 35.0,
        "packet_loss": 0.0,
        "jitter": 2.0,
        "download_bandwidth": 60.0,
        "upload_bandwidth": 20.0,
        "traffic_rate": 300.0,
        "network_utilization": 20.0,
        "connection_type": "Wi-Fi",
        "signal_strength": 80.0
    }
    resp = prediction_engine.predict_telemetry(telem)
    probs = resp.class_probabilities
    assert sum(probs.values()) == pytest.approx(1.0, abs=1e-2)
    assert resp.predicted_class in ["GOOD", "MODERATE", "POOR"]
    assert 0.0 <= resp.confidence <= 1.0


def test_explainability_contributing_factors():
    """Ensure poor telemetry triggers explainable contributing factors."""
    poor_telem = {
        "latency": 250.0,
        "packet_loss": 12.0,
        "jitter": 40.0,
        "download_bandwidth": 1.0,
        "upload_bandwidth": 0.5,
        "traffic_rate": 10.0,
        "network_utilization": 95.0,
        "connection_type": "Wi-Fi",
        "signal_strength": 20.0
    }
    resp = prediction_engine.predict_telemetry(poor_telem)
    assert resp.predicted_class == "POOR"
    factors = resp.explanation.contributing_factors
    assert len(factors) > 0
    assert any("loss" in f.lower() or "latency" in f.lower() for f in factors)
    assert resp.explanation.disclaimer is not None
