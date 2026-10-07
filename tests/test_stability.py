"""Unit tests for Network Stability Score Engine."""

import sys
from pathlib import Path
import pytest

backend_root = Path(__file__).resolve().parent.parent / "backend"
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.ml.stability import NetworkStabilityEngine


def test_stability_score_ideal_conditions():
    """Pristine low latency, zero loss should yield near 100/100 score."""
    score = NetworkStabilityEngine.calculate_score(
        latency=15.0,
        packet_loss=0.0,
        jitter=1.0,
        download_bandwidth=100.0,
        upload_bandwidth=50.0,
        network_utilization=10.0,
        signal_strength=95.0
    )
    assert score >= 95.0


def test_stability_score_severe_loss_penalty():
    """Severe packet loss (e.g. 15%) should drastically degrade stability score."""
    score = NetworkStabilityEngine.calculate_score(
        latency=250.0,
        packet_loss=15.0,
        jitter=45.0,
        download_bandwidth=1.0,
        upload_bandwidth=0.2,
        network_utilization=95.0,
        signal_strength=20.0
    )
    assert score <= 30.0


def test_stability_score_ethernet_null_signal():
    """Ethernet with null signal should not be unfairly penalized for missing RSSI."""
    score = NetworkStabilityEngine.calculate_score(
        latency=15.0,
        packet_loss=0.0,
        jitter=1.0,
        download_bandwidth=100.0,
        upload_bandwidth=50.0,
        network_utilization=10.0,
        signal_strength=None
    )
    assert score == 100.0
