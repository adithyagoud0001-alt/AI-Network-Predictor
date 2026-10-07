"""FastAPI REST API Routes

Implements the standard endpoints for network telemetry, predictions,
historical logs, alerts, interface management, and model metadata.
"""

from typing import List, Optional, Dict, Any
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database import crud
from app.schemas.network import (
    NetworkTelemetry,
    NetworkInterfaceInfo,
    CollectorStatus
)
from app.schemas.prediction import (
    PredictRequest,
    PredictResponse,
    ModelMetadataResponse
)
from app.schemas.alert import AlertItem, AlertListResponse
from app.collector.telemetry import telemetry_service
from app.ml.service import prediction_engine
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", summary="Service Health Check")
def get_health() -> Dict[str, Any]:
    """Returns system status, model state, and collector state."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "collector_running": telemetry_service.is_running,
        "model_loaded": prediction_engine.pipeline is not None,
        "champion_model": prediction_engine.metadata.get("champion_model_name", "Random Forest")
    }


@router.get("/network/interfaces", response_model=List[NetworkInterfaceInfo], summary="Available Network Interfaces")
def list_network_interfaces() -> List[NetworkInterfaceInfo]:
    """Enumerates available physical and virtual network interfaces."""
    return telemetry_service.get_interfaces()


@router.post("/network/interface/select", summary="Select Active Interface")
def select_interface(interface_name: Optional[str] = Query(None, description="Interface name or empty for auto-detect")) -> Dict[str, Any]:
    """Configures the network collector to monitor a specific interface."""
    telemetry_service.set_interface(interface_name)
    return {
        "status": "success",
        "selected_interface": interface_name or "auto-detect"
    }


@router.get("/network/current", response_model=NetworkTelemetry, summary="Current Telemetry Snapshot")
def get_current_telemetry() -> NetworkTelemetry:
    """Returns the latest captured network telemetry snapshot."""
    latest = telemetry_service.get_latest_telemetry()
    if latest is None:
        # Collect immediately if buffer empty
        latest = telemetry_service.collect_now()
    return latest


@router.post("/network/collect-now", response_model=NetworkTelemetry, summary="Trigger Immediate Telemetry Snapshot")
def trigger_snapshot() -> NetworkTelemetry:
    """Forces an immediate telemetry measurement cycle."""
    return telemetry_service.collect_now()


@router.get("/network/history", response_model=List[NetworkTelemetry], summary="Historical Telemetry Snapshots")
def get_telemetry_history(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
) -> List[NetworkTelemetry]:
    """Queries chronological network telemetry history."""
    # First try database, fall back to in-memory buffer
    db_rows = crud.get_recent_measurements(db, limit=limit)
    if db_rows:
        return [NetworkTelemetry.model_validate(r) for r in db_rows]
    return telemetry_service.get_telemetry_history(limit=limit)


@router.post("/predict", response_model=PredictResponse, summary="Predict Connection Quality from Features")
def predict_quality(
    request: PredictRequest,
    db: Session = Depends(get_db)
) -> PredictResponse:
    """Computes AI connection quality prediction, confidence, stability score, and explanation."""
    req_dict = request.model_dump()
    response = prediction_engine.predict_telemetry(req_dict)

    # Persist prediction in DB
    try:
        crud.create_prediction(db, interface=request.interface or "manual", prediction=response)
    except Exception as exc:
        logger.error(f"Failed to persist prediction: {exc}")

    return response


@router.get("/prediction/latest", response_model=PredictResponse, summary="Latest AI Prediction")
def get_latest_prediction(db: Session = Depends(get_db)) -> PredictResponse:
    """Returns the latest prediction for the current active network state."""
    current_telem = telemetry_service.get_latest_telemetry()
    if current_telem is None:
        current_telem = telemetry_service.collect_now()

    response = prediction_engine.predict_telemetry(
        current_telem.model_dump(),
        recent_history=telemetry_service.get_telemetry_history(5)
    )
    return response


@router.get("/model/info", response_model=ModelMetadataResponse, summary="Model Metadata & Performance")
def get_model_info() -> ModelMetadataResponse:
    """Returns model version, algorithm comparisons, cross-validation metrics, and feature importances."""
    return prediction_engine.get_metadata_response()


@router.get("/alerts", response_model=AlertListResponse, summary="Active Degradation Alerts")
def get_active_alerts(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> AlertListResponse:
    """Returns active and recent network degradation alerts."""
    # Check current telemetry history for active trends
    history = telemetry_service.get_telemetry_history(6)
    latest_pred = prediction_engine.predict_telemetry(history[-1].model_dump()) if history else None
    current_class = latest_pred.predicted_class if latest_pred else "GOOD"

    trend_alerts = prediction_engine.degradation_detector.analyze_trend(
        history=history,
        current_prediction=current_class
    )

    alert_items = [
        AlertItem(
            timestamp=a.timestamp,
            severity=a.severity,
            title=a.title,
            message=a.message,
            metric=a.metric,
            current_value=a.current_value,
            threshold=a.threshold,
            trend_direction=a.trend_direction
        )
        for a in trend_alerts
    ]

    return AlertListResponse(
        total_alerts=len(alert_items),
        active_alerts=alert_items
    )


@router.post("/monitoring/start", summary="Start Background Telemetry Collection")
def start_monitoring() -> Dict[str, Any]:
    """Starts the continuous background network telemetry collector."""
    telemetry_service.start()
    return {"status": "started", "collector_running": True}


@router.post("/monitoring/stop", summary="Stop Background Telemetry Collection")
async def stop_monitoring() -> Dict[str, Any]:
    """Stops the continuous background network telemetry collector."""
    await telemetry_service.stop()
    return {"status": "stopped", "collector_running": False}


@router.get("/collector/status", response_model=CollectorStatus, summary="Collector Status")
def get_collector_status() -> CollectorStatus:
    return telemetry_service.get_status()
