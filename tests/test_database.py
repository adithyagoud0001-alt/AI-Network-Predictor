"""Unit tests for Database Operations and Models."""

from datetime import datetime, timezone
import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

backend_root = Path(__file__).resolve().parent.parent / "backend"
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.database.connection import Base
from app.database import crud
from app.schemas.network import NetworkTelemetry
from app.schemas.prediction import PredictResponse, PredictionExplanation
from app.ml.degradation import DegradationAlert


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_database_crud_flow(test_db):
    """Test full create and read flow for measurements, predictions, and alerts."""
    # 1. Create Telemetry measurement
    telem = NetworkTelemetry(
        timestamp=datetime.now(timezone.utc),
        interface="eth0",
        connection_type="Ethernet",
        latency=12.5,
        packet_loss=0.0,
        jitter=1.1,
        download_bandwidth=100.0,
        upload_bandwidth=50.0,
        signal_strength=None,
        bytes_sent=5000,
        bytes_received=15000,
        packets_sent=50,
        packets_received=120,
        traffic_rate=200.0,
        network_utilization=15.0
    )
    meas = crud.create_measurement(test_db, telem)
    assert meas.id is not None
    assert meas.interface == "eth0"

    # Query recent measurements
    recents = crud.get_recent_measurements(test_db, interface="eth0")
    assert len(recents) == 1
    assert recents[0].latency == 12.5

    # 2. Create Prediction
    pred_resp = PredictResponse(
        timestamp=datetime.now(timezone.utc),
        predicted_class="GOOD",
        confidence=0.98,
        confidence_percentage=98.0,
        class_probabilities={"GOOD": 0.98, "MODERATE": 0.01, "POOR": 0.01},
        stability_score=95.0,
        stability_grade="EXCELLENT",
        explanation=PredictionExplanation(
            predicted_class="GOOD",
            confidence=0.98,
            confidence_percentage=98.0,
            contributing_factors=["Low latency (12.5 ms)"],
            disclaimer="Test disclaimer"
        )
    )
    pred_row = crud.create_prediction(test_db, interface="eth0", prediction=pred_resp)
    assert pred_row.id is not None
    assert pred_row.predicted_class == "GOOD"

    # Query latest prediction
    latest_pred = crud.get_latest_prediction(test_db, interface="eth0")
    assert latest_pred is not None
    assert latest_pred.confidence == 0.98

    # 3. Create Alert
    alert = DegradationAlert(
        severity="WARNING",
        title="High Latency Warning",
        message="Latency exceeded threshold",
        metric="latency",
        current_value=125.0,
        threshold=100.0
    )
    alert_row = crud.create_alert(test_db, alert)
    assert alert_row.id is not None

    alerts = crud.get_recent_alerts(test_db)
    assert len(alerts) == 1
    assert alerts[0].title == "High Latency Warning"
