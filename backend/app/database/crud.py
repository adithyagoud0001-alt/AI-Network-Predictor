"""Database CRUD Operations Module"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.models import (
    NetworkMeasurementModel,
    PredictionModel,
    AlertModel
)
from app.schemas.network import NetworkTelemetry
from app.schemas.prediction import PredictResponse
from app.ml.degradation import DegradationAlert


def create_measurement(db: Session, telemetry: NetworkTelemetry) -> NetworkMeasurementModel:
    meas = NetworkMeasurementModel(
        timestamp=telemetry.timestamp,
        interface=telemetry.interface,
        connection_type=telemetry.connection_type,
        latency=telemetry.latency,
        min_latency=telemetry.min_latency,
        max_latency=telemetry.max_latency,
        packet_loss=telemetry.packet_loss,
        jitter=telemetry.jitter,
        download_bandwidth=telemetry.download_bandwidth,
        upload_bandwidth=telemetry.upload_bandwidth,
        signal_strength=telemetry.signal_strength,
        bytes_sent=telemetry.bytes_sent,
        bytes_received=telemetry.bytes_received,
        packets_sent=telemetry.packets_sent,
        packets_received=telemetry.packets_received,
        traffic_rate=telemetry.traffic_rate,
        network_utilization=telemetry.network_utilization
    )
    db.add(meas)
    db.commit()
    db.refresh(meas)
    return meas


def get_recent_measurements(
    db: Session,
    interface: Optional[str] = None,
    limit: int = 50
) -> List[NetworkMeasurementModel]:
    query = db.query(NetworkMeasurementModel)
    if interface:
        query = query.filter(NetworkMeasurementModel.interface == interface)
    return query.order_by(desc(NetworkMeasurementModel.timestamp)).limit(limit).all()[::-1]


def create_prediction(
    db: Session,
    interface: str,
    prediction: PredictResponse
) -> PredictionModel:
    pred = PredictionModel(
        timestamp=prediction.timestamp,
        interface=interface,
        predicted_class=prediction.predicted_class,
        confidence=prediction.confidence,
        class_probabilities=prediction.class_probabilities,
        stability_score=prediction.stability_score,
        stability_grade=prediction.stability_grade,
        contributing_factors=prediction.explanation.contributing_factors,
        model_version=prediction.model_version
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)
    return pred


def get_latest_prediction(db: Session, interface: Optional[str] = None) -> Optional[PredictionModel]:
    query = db.query(PredictionModel)
    if interface:
        query = query.filter(PredictionModel.interface == interface)
    return query.order_by(desc(PredictionModel.timestamp)).first()


def get_prediction_history(db: Session, limit: int = 50) -> List[PredictionModel]:
    return db.query(PredictionModel).order_by(desc(PredictionModel.timestamp)).limit(limit).all()[::-1]


def create_alert(db: Session, alert: DegradationAlert) -> AlertModel:
    al = AlertModel(
        timestamp=alert.timestamp,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        metric=alert.metric,
        current_value=alert.current_value,
        threshold=alert.threshold
    )
    db.add(al)
    db.commit()
    db.refresh(al)
    return al


def get_recent_alerts(db: Session, limit: int = 20) -> List[AlertModel]:
    return db.query(AlertModel).order_by(desc(AlertModel.timestamp)).limit(limit).all()
