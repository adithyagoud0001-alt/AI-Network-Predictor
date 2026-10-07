"""Integration tests for FastAPI endpoints."""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_root = Path(__file__).resolve().parent.parent / "backend"
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.main import app
from app.database.connection import Base, engine


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_and_health(client):
    """Test root and health endpoints."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "operational"

    health = client.get("/api/v1/health")
    assert health.status_code == 200
    data = health.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert "champion_model" in data


def test_list_interfaces(client):
    """Test interface enumeration."""
    resp = client.get("/api/v1/network/interfaces")
    assert resp.status_code == 200
    interfaces = resp.json()
    assert isinstance(interfaces, list)
    assert len(interfaces) > 0


def test_predict_endpoint(client):
    """Test manual prediction endpoint with custom telemetry."""
    # 1. Good connection payload
    good_payload = {
        "latency": 15.0,
        "packet_loss": 0.0,
        "jitter": 1.2,
        "download_bandwidth": 85.0,
        "upload_bandwidth": 30.0,
        "traffic_rate": 500.0,
        "network_utilization": 25.0,
        "connection_type": "Ethernet",
        "signal_strength": None
    }
    resp = client.post("/api/v1/predict", json=good_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["predicted_class"] == "GOOD"
    assert data["confidence"] > 0.7
    assert data["stability_score"] > 85.0
    assert "explanation" in data
    assert len(data["explanation"]["contributing_factors"]) > 0

    # 2. Poor connection payload (high loss and high latency)
    poor_payload = {
        "latency": 220.0,
        "packet_loss": 18.0,
        "jitter": 45.0,
        "download_bandwidth": 1.5,
        "upload_bandwidth": 0.5,
        "traffic_rate": 20.0,
        "network_utilization": 95.0,
        "connection_type": "Wi-Fi",
        "signal_strength": 25.0
    }
    resp_poor = client.post("/api/v1/predict", json=poor_payload)
    assert resp_poor.status_code == 200
    poor_data = resp_poor.json()
    assert poor_data["predicted_class"] == "POOR"
    assert poor_data["stability_score"] < 50.0


def test_model_info_endpoint(client):
    """Test model metadata endpoint."""
    resp = client.get("/api/v1/model/info")
    assert resp.status_code == 200
    info = resp.json()
    assert info["model_version"] == "1.0.0"
    assert "champion_model_name" in info
    assert len(info["validation_comparison"]) == 5
    assert len(info["global_feature_importances"]) > 0


def test_alerts_endpoint(client):
    """Test alerts endpoint."""
    resp = client.get("/api/v1/alerts")
    assert resp.status_code == 200
    assert "active_alerts" in resp.json()
