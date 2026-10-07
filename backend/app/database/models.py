"""SQLAlchemy Database ORM Models

Defines tables for network telemetry, predictions, alerts, and model metadata.
Includes indices on timestamp and interface for high-performance historical queries.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, Text, JSON, Index, Boolean
from app.database.connection import Base


class NetworkMeasurementModel(Base):
    __tablename__ = "network_measurements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    interface = Column(String(64), nullable=False, index=True)
    connection_type = Column(String(32), default="Unknown")
    
    latency = Column(Float, nullable=False)
    min_latency = Column(Float, nullable=True)
    max_latency = Column(Float, nullable=True)
    packet_loss = Column(Float, nullable=False)
    jitter = Column(Float, nullable=False)
    
    download_bandwidth = Column(Float, nullable=False)
    upload_bandwidth = Column(Float, nullable=False)
    signal_strength = Column(Float, nullable=True)  # Null for Ethernet
    
    bytes_sent = Column(Integer, nullable=False)
    bytes_received = Column(Integer, nullable=False)
    packets_sent = Column(Integer, nullable=False)
    packets_received = Column(Integer, nullable=False)
    
    traffic_rate = Column(Float, nullable=False)
    network_utilization = Column(Float, nullable=False)

    __table_args__ = (
        Index("idx_meas_iface_time", "interface", "timestamp"),
    )


class PredictionModel(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    interface = Column(String(64), nullable=False, index=True)
    
    predicted_class = Column(String(32), nullable=False)  # GOOD, MODERATE, POOR
    confidence = Column(Float, nullable=False)
    class_probabilities = Column(JSON, nullable=False)
    stability_score = Column(Float, nullable=False)
    stability_grade = Column(String(32), nullable=False)
    
    contributing_factors = Column(JSON, nullable=False)
    model_version = Column(String(32), default="1.0.0")

    __table_args__ = (
        Index("idx_pred_iface_time", "interface", "timestamp"),
    )


class AlertModel(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    severity = Column(String(32), nullable=False)  # INFO, WARNING, CRITICAL
    title = Column(String(128), nullable=False)
    message = Column(Text, nullable=False)
    metric = Column(String(64), nullable=True)
    current_value = Column(Float, nullable=True)
    threshold = Column(Float, nullable=True)
    acknowledged = Column(Boolean, default=False)


class ModelMetadataModel(Base):
    __tablename__ = "model_metadata"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    version = Column(String(32), nullable=False)
    champion_model_name = Column(String(64), nullable=False)
    metrics_summary = Column(JSON, nullable=False)
