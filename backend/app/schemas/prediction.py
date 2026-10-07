"""Prediction and Model Schemas

Pydantic schemas for ML inferences, probability distributions, stability scores,
explanations, and model information.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    latency: float = Field(..., ge=0.0, description="Round-trip latency in ms")
    packet_loss: float = Field(..., ge=0.0, le=100.0, description="Packet loss %")
    jitter: float = Field(..., ge=0.0, description="Packet delay variation in ms")
    download_bandwidth: float = Field(default=25.0, ge=0.0, description="Download throughput in Mbps")
    upload_bandwidth: float = Field(default=10.0, ge=0.0, description="Upload throughput in Mbps")
    traffic_rate: float = Field(default=500.0, ge=0.0, description="Traffic rate in KB/s")
    network_utilization: float = Field(default=20.0, ge=0.0, le=100.0, description="Utilization %")
    connection_type: str = Field(default="Ethernet", description="Wi-Fi, Ethernet, etc.")
    signal_strength: Optional[float] = Field(default=None, description="Wi-Fi signal %, None for Ethernet")
    interface: Optional[str] = Field(default="default", description="Interface name")


class PredictionExplanation(BaseModel):
    predicted_class: str
    confidence: float
    confidence_percentage: float
    contributing_factors: List[str]
    disclaimer: str


class FuturePredictionForecast(BaseModel):
    """Architectural extension schema for future-horizon prediction (Section 13)."""
    horizon_seconds: int = 30
    forecasted_state: str
    stability_trend: str  # "STABLE", "DEGRADING", "IMPROVING"
    forecast_confidence: float
    methodology: str = "Linear trend extrapolation & QoS risk projection"


class PredictResponse(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    predicted_class: str  # GOOD, MODERATE, POOR
    confidence: float
    confidence_percentage: float
    class_probabilities: Dict[str, float]
    stability_score: float
    stability_grade: str  # EXCELLENT, STABLE, DEGRADED, CRITICAL
    explanation: PredictionExplanation
    future_forecast: Optional[FuturePredictionForecast] = None
    model_version: str = "1.0.0"
    model_name: str = "Random Forest"


class ModelMetadataResponse(BaseModel):
    model_version: str
    timestamp: str
    champion_model_name: str
    classes: List[str]
    input_features: List[str]
    validation_comparison: List[Dict[str, Any]]
    champion_test_metrics: Dict[str, Any]
    global_feature_importances: List[Dict[str, Any]]
    pipeline_file: str
