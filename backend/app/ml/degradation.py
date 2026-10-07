"""Network Degradation Detection and Early Warning Engine

Monitors rolling telemetry windows to detect adverse networking trends
(latency inflation, jitter surge, packet loss spikes, bufferbloat queues)
and emits proactive early warnings before catastrophic connection failure occurs.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import numpy as np

from app.schemas.network import NetworkTelemetry
from app.config import settings


class DegradationAlert:
    def __init__(
        self,
        severity: str,  # "INFO", "WARNING", "CRITICAL"
        title: str,
        message: str,
        timestamp: Optional[datetime] = None,
        metric: Optional[str] = None,
        current_value: Optional[float] = None,
        threshold: Optional[float] = None,
        trend_direction: Optional[str] = None
    ):
        self.severity = severity
        self.title = title
        self.message = message
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.metric = metric
        self.current_value = current_value
        self.threshold = threshold
        self.trend_direction = trend_direction

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "metric": self.metric,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "trend_direction": self.trend_direction
        }


class NetworkDegradationDetector:
    """Analyzes recent telemetry history to detect degradation trends."""

    def __init__(self, min_window_samples: int = 4):
        self.min_window_samples = min_window_samples

    def analyze_trend(
        self,
        history: List[NetworkTelemetry],
        current_prediction: Optional[str] = None
    ) -> List[DegradationAlert]:
        """Examines recent telemetry for degradation and trend shifts."""
        alerts: List[DegradationAlert] = []

        if len(history) < self.min_window_samples:
            return alerts

        recent = history[-self.min_window_samples:]
        current = recent[-1]

        latencies = [s.latency for s in recent]
        losses = [s.packet_loss for s in recent]
        jitters = [s.jitter for s in recent]
        downloads = [s.download_bandwidth for s in recent]
        utils = [s.network_utilization for s in recent]

        # 1. Packet Loss Spike Check
        if current.packet_loss >= settings.PACKET_LOSS_DEGRADATION_THRESHOLD:
            alerts.append(DegradationAlert(
                severity="CRITICAL",
                title="Critical Packet Loss Detected",
                message=f"Packet loss has reached {current.packet_loss:.1f}%, exceeding tolerable threshold of {settings.PACKET_LOSS_DEGRADATION_THRESHOLD}%. TCP retransmissions will collapse throughput.",
                metric="packet_loss",
                current_value=current.packet_loss,
                threshold=settings.PACKET_LOSS_DEGRADATION_THRESHOLD,
                trend_direction="increasing"
            ))
        elif current.packet_loss > 1.0 and current_prediction == "GOOD":
            alerts.append(DegradationAlert(
                severity="WARNING",
                title="Packet Loss Escalation",
                message=f"Intermittent packet loss ({current.packet_loss:.1f}%) observed on {current.interface}. Connection quality is at risk of degrading from GOOD to MODERATE.",
                metric="packet_loss",
                current_value=current.packet_loss,
                threshold=1.0,
                trend_direction="increasing"
            ))

        # 2. Latency Trend Analysis (Linear slope)
        x = np.arange(len(latencies))
        lat_slope = float(np.polyfit(x, latencies, 1)[0]) if len(latencies) >= 2 else 0.0

        if current.latency >= settings.LATENCY_DEGRADATION_THRESHOLD_MS:
            alerts.append(DegradationAlert(
                severity="CRITICAL" if current.latency > 200.0 else "WARNING",
                title="High Latency Alert",
                message=f"Latency elevated to {current.latency:.1f} ms. Real-time applications (VoIP, interactive gaming) will experience noticeable lag.",
                metric="latency",
                current_value=current.latency,
                threshold=settings.LATENCY_DEGRADATION_THRESHOLD_MS,
                trend_direction="increasing"
            ))
        elif lat_slope > 8.0 and current_prediction == "GOOD":
            alerts.append(DegradationAlert(
                severity="WARNING",
                title="Latency Deterioration Detected",
                message=f"RTT is steadily climbing (+{lat_slope:.1f} ms/interval). Connection is likely to transition from GOOD to MODERATE.",
                metric="latency",
                current_value=current.latency,
                trend_direction="increasing"
            ))

        # 3. Jitter Surge Check
        if current.jitter >= settings.JITTER_DEGRADATION_THRESHOLD_MS:
            alerts.append(DegradationAlert(
                severity="WARNING",
                title="Elevated Jitter Warning",
                message=f"Packet delay variation is {current.jitter:.1f} ms. Jitter buffers may suffer underruns.",
                metric="jitter",
                current_value=current.jitter,
                threshold=settings.JITTER_DEGRADATION_THRESHOLD_MS,
                trend_direction="increasing"
            ))

        # 4. Link Congestion / Bufferbloat
        if current.network_utilization > 90.0 and lat_slope > 5.0:
            alerts.append(DegradationAlert(
                severity="WARNING",
                title="Bufferbloat / Link Congestion",
                message=f"Network utilization is {current.network_utilization:.1f}% with rising latency, indicating packet queue buildup at the interface/gateway bottleneck.",
                metric="network_utilization",
                current_value=current.network_utilization,
                threshold=90.0,
                trend_direction="increasing"
            ))

        return alerts
