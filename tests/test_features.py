"""Unit tests for Feature Engineering & Preprocessing Pipelines."""

import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

backend_root = Path(__file__).resolve().parent.parent / "backend"
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.ml.features import FeatureEngineer, StreamingFeatureEngineer, ALL_MODEL_FEATURES
from app.ml.preprocessor import build_preprocessor


def test_streaming_feature_engineer_edge_cases():
    """Test feature extraction with edge cases: 100% loss, zero bandwidth, missing RSSI."""
    engineer = StreamingFeatureEngineer(window_size=5)

    # 1. Edge case: 100% loss, high latency, zero bandwidth, missing RSSI
    telem = {
        "latency": 500.0,
        "packet_loss": 100.0,
        "jitter": 60.0,
        "download_bandwidth": 0.0,
        "upload_bandwidth": 0.0,
        "traffic_rate": 0.0,
        "network_utilization": 0.0,
        "connection_type": "Ethernet",
        "signal_strength": None
    }
    feats = engineer.transform_single(telem)

    assert feats["latency"] == 500.0
    assert feats["packet_loss"] == 100.0
    assert feats["signal_strength_missing"] == 1.0
    assert feats["signal_strength_imputed"] == 0.0
    assert feats["download_bandwidth"] == 0.0

    # Ensure all model features exist
    for f in ALL_MODEL_FEATURES:
        assert f in feats, f"Missing feature: {f}"


def test_batch_feature_engineer_no_future_leakage():
    """Verify rolling transformations do not leak future information."""
    raw_df = pd.DataFrame([
        {"timestamp": "2026-10-07T10:00:00Z", "latency": 10.0, "packet_loss": 0.0, "jitter": 1.0, "download_bandwidth": 50.0, "upload_bandwidth": 20.0, "network_utilization": 15.0, "signal_strength": None, "connection_type": "Ethernet"},
        {"timestamp": "2026-10-07T10:00:05Z", "latency": 20.0, "packet_loss": 0.0, "jitter": 2.0, "download_bandwidth": 60.0, "upload_bandwidth": 20.0, "network_utilization": 20.0, "signal_strength": None, "connection_type": "Ethernet"},
        {"timestamp": "2026-10-07T10:00:10Z", "latency": 300.0, "packet_loss": 50.0, "jitter": 40.0, "download_bandwidth": 1.0, "upload_bandwidth": 0.5, "network_utilization": 95.0, "signal_strength": None, "connection_type": "Ethernet"},
    ])

    df = FeatureEngineer.engineer_batch_dataframe(raw_df, window_size=2)
    # The first row's rolling mean should equal its own latency (10.0), NOT future 20 or 300
    assert df.loc[0, "latency_rolling_mean"] == 10.0
    # Second row rolling mean over window=2 should be (10+20)/2 = 15.0
    assert df.loc[1, "latency_rolling_mean"] == 15.0


def test_preprocessor_pipeline_transform():
    """Verify ColumnTransformer handles numeric scaling and categorical encoding without crashing."""
    preprocessor = build_preprocessor()

    dummy_data = pd.DataFrame([{
        "latency": 25.0,
        "packet_loss": 0.0,
        "jitter": 2.5,
        "download_bandwidth": 50.0,
        "upload_bandwidth": 15.0,
        "traffic_rate": 200.0,
        "network_utilization": 25.0,
        "latency_rolling_mean": 25.0,
        "latency_rolling_std": 0.0,
        "packet_loss_rolling_mean": 0.0,
        "jitter_rolling_mean": 2.5,
        "latency_change_rate": 0.0,
        "packet_loss_change_rate": 0.0,
        "bandwidth_trend": 0.0,
        "traffic_utilization_ratio": 0.25,
        "signal_strength_imputed": 0.0,
        "signal_strength_missing": 1.0,
        "connection_type": "Ethernet"
    }])

    # Fit and transform
    transformed = preprocessor.fit_transform(dummy_data)
    assert transformed is not None
    assert transformed.shape[0] == 1
    assert not np.isnan(transformed).any()
