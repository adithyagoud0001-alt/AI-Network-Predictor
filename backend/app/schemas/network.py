"""Network Telemetry Pydantic Schemas

Defines structured, validated schemas for network telemetry data,
network interfaces, and collector parameters.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class NetworkInterfaceInfo(BaseModel):
    name: str
    is_up: bool
    speed_mbps: Optional[float] = None
    mtu: Optional[int] = None
    addresses: List[str] = Field(default_factory=list)
    connection_type: str = "Unknown"  # "Wi-Fi", "Ethernet", "Cellular", "Virtual", "Loopback"
    is_default: bool = False


class NetworkTelemetry(BaseModel):
    """Core network telemetry snapshot at a given timestamp."""
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    interface: str
    connection_type: str = "Unknown"  # "Wi-Fi", "Ethernet", etc.
    
    # RTT / Latency metrics (milliseconds)
    latency: float = Field(..., description="Average round-trip latency in ms")
    min_latency: Optional[float] = Field(None, description="Minimum latency in sample batch in ms")
    max_latency: Optional[float] = Field(None, description="Maximum latency in sample batch in ms")
    
    # Packet Loss
    packet_loss: float = Field(..., ge=0.0, le=100.0, description="Packet loss percentage (0.0 to 100.0)")
    
    # Jitter (milliseconds)
    jitter: float = Field(..., ge=0.0, description="Packet delay variation in ms")
    rfc3550_jitter: Optional[float] = Field(None, description="RFC 3550 smoothed jitter in ms")
    
    # Bandwidth & Traffic metrics
    download_bandwidth: float = Field(..., ge=0.0, description="Current or estimated download throughput in Mbps")
    upload_bandwidth: float = Field(..., ge=0.0, description="Current or estimated upload throughput in Mbps")
    
    # Wi-Fi Signal Strength (None for Ethernet / unsupported interfaces)
    signal_strength: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=100.0, 
        description="Wi-Fi signal strength percentage (0-100%), None for Ethernet"
    )
    signal_strength_dbm: Optional[float] = Field(
        None,
        description="Wi-Fi signal RSSI in dBm (-100 to -30 dBm), None if unavailable"
    )
    
    # Interface Counter Totals
    bytes_sent: int = Field(..., ge=0, description="Cumulative bytes transmitted on interface")
    bytes_received: int = Field(..., ge=0, description="Cumulative bytes received on interface")
    packets_sent: int = Field(..., ge=0, description="Cumulative packets transmitted on interface")
    packets_received: int = Field(..., ge=0, description="Cumulative packets received on interface")
    
    # Rates and Utilization
    traffic_rate: float = Field(..., ge=0.0, description="Aggregate traffic rate in KB/s")
    traffic_rate_mbps: Optional[float] = Field(None, ge=0.0, description="Aggregate traffic rate in Mbps")
    network_utilization: float = Field(
        ..., 
        ge=0.0, 
        le=100.0, 
        description="Interface link utilization percentage (0.0 to 100.0)"
    )


class CollectorStatus(BaseModel):
    is_running: bool
    active_interface: Optional[str] = None
    target_host: str
    interval_seconds: float
    total_samples_collected: int = 0
    last_collection_time: Optional[datetime] = None
