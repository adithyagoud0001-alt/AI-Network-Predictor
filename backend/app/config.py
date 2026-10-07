"""Application Configuration Module

Manages environment variables, defaults, and configuration settings
for the AI-Based Network Connection Predictor.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "AI-Based Network Connection Predictor"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    # Supports SQLite (default for instant setup) and PostgreSQL (for production/Docker)
    DATABASE_URL: str = "sqlite:///./network_predictor.db"

    # Telemetry Collector Settings
    COLLECTOR_INTERVAL_SECONDS: float = 5.0
    DEFAULT_PING_TARGET: str = "8.8.8.8"
    SECONDARY_PING_TARGET: str = "1.1.1.1"
    PING_COUNT: int = 5
    PING_TIMEOUT_SECONDS: float = 2.0

    # Degradation Detection & Alert Thresholds
    LATENCY_DEGRADATION_THRESHOLD_MS: float = 120.0
    PACKET_LOSS_DEGRADATION_THRESHOLD: float = 5.0
    JITTER_DEGRADATION_THRESHOLD_MS: float = 25.0
    STABILITY_ALERT_THRESHOLD: float = 60.0

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
