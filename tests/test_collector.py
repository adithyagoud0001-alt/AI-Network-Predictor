"""Unit tests for the platform-specific Network Telemetry Collector."""

import sys
from pathlib import Path
import pytest

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.collector.telemetry import create_platform_collector, NetworkTelemetryService
from app.schemas.network import NetworkTelemetry, NetworkInterfaceInfo


def test_platform_collector_creation():
    """Verify factory returns an OS-appropriate collector."""
    collector = create_platform_collector()
    assert collector is not None
    assert collector.target_host == "8.8.8.8"


def test_interface_discovery():
    """Verify network interfaces can be detected on current OS."""
    collector = create_platform_collector()
    interfaces = collector.get_all_interfaces()
    assert len(interfaces) > 0
    # Check that at least one interface has valid properties
    first_iface = interfaces[0]
    assert isinstance(first_iface, NetworkInterfaceInfo)
    assert isinstance(first_iface.name, str)
    assert isinstance(first_iface.is_up, bool)


def test_real_ping_measurement():
    """Verify ping executes against a reliable public DNS IP."""
    collector = create_platform_collector()
    rtts, loss = collector.ping_host("8.8.8.8", count=2, timeout_secs=1.5)
    assert isinstance(rtts, list)
    assert 0.0 <= loss <= 100.0
    if loss < 100.0:
        assert len(rtts) > 0
        for rtt in rtts:
            assert rtt > 0.0


def test_real_telemetry_snapshot():
    """Verify that collect_snapshot returns a valid NetworkTelemetry schema."""
    collector = create_platform_collector()
    snapshot = collector.collect_snapshot()
    assert isinstance(snapshot, NetworkTelemetry)
    assert snapshot.latency >= 0.0
    assert 0.0 <= snapshot.packet_loss <= 100.0
    assert snapshot.jitter >= 0.0
    assert snapshot.traffic_rate >= 0.0
    assert 0.0 <= snapshot.network_utilization <= 100.0

    # Ensure RSSI is either a valid percentage or None (if Ethernet/unsupported), not an invented value
    if snapshot.signal_strength is not None:
        assert 0.0 <= snapshot.signal_strength <= 100.0
