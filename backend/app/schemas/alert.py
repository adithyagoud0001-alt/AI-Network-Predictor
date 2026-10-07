"""Alert Pydantic Schemas

Schemas for degradation warnings, early warnings, and network status notifications.
"""

from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field


class AlertItem(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    severity: str  # "INFO", "WARNING", "CRITICAL"
    title: str
    message: str
    metric: Optional[str] = None
    current_value: Optional[float] = None
    threshold: Optional[float] = None
    trend_direction: Optional[str] = None


class AlertListResponse(BaseModel):
    total_alerts: int
    active_alerts: List[AlertItem]
