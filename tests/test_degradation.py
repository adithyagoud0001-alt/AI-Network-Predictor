"""Unit tests for Network Degradation and Early Warning Alert Logic."""

from datetime import datetime, timezone
import sys
from pathlib import Path
import pytest

backend_root = Path(__file__).resolve().parent.parent / "backend"
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.ml.degradation import NetworkDegradationDetector
from app.schemas.network import NetworkTelemetry


def make_dummy_telemetry(latency: float, packet_loss: float, jitter: float, util: float = 20.0):
    return NetworkTelemetry(
        timestamp=datetime.now(timezone.utc),
        interface="eth0",
        connection_type="Ethernet",
        latency=latency,
        packet_loss=packet_loss,
        jitter=jitter,
        download_bandwidth=50.0,
        upload_bandwidth=20.0,
        signal_strength=None,
        bytes_sent=1000,
        bytes_received=2000,
        packets_sent=100,
        packets_received=200,
        traffic_rate=50.0,
        network_utilization=util
    )


def test_degradation_detector_nominal():
    """Stable connection history should produce no degradation alerts."""
    detector = NetworkDegradationDetector(min_window_samples=3)
    history = [
        make_dummy_telemetry(15.0, 0.0, 1.0),
        make_dummy_telemetry(16.0, 0.0, 1.2),
        make_dummy_telemetry(15.5, 0.0, 1.1),
    ]
    alerts = detector.analyze_trend(history, current_prediction="GOOD")
    assert len(alerts) == 0


def test_degradation_detector_rising_latency_alert():
    """Steep latency slope while currently GOOD should trigger early warning."""
    detector = NetworkDegradationDetector(min_window_samples=4)
    history = [
        make_dummy_telemetry(20.0, 0.0, 2.0),
        make_dummy_telemetry(35.0, 0.0, 4.0),
        make_dummy_telemetry(55.0, 0.0, 6.0),
        make_dummy_telemetry(80.0, 0.0, 8.0),
    ]
    alerts = detector.analyze_trend(history, current_prediction="GOOD")
    assert len(alerts) > 0
    assert any("transition" in a.message.lower() or "latency" in a.title.lower() for a in alerts)


def test_degradation_detector_critical_packet_loss():
    """Severe packet loss should trigger CRITICAL alert."""
    detector = NetworkDegradationDetector(min_window_samples=3)
    history = [
        make_dummy_telemetry(20.0, 0.0, 2.0),
        make_dummy_telemetry(30.0, 2.0, 5.0),
        make_dummy_telemetry(60.0, 8.5, 12.0),  # > 5% threshold
    ]
    alerts = detector.analyze_trend(history, current_prediction="MODERATE")
    assert any(a.severity == "CRITICAL" for a in alerts)
