"""Abstract Base Class for Platform-Specific Network Telemetry Collectors

Defines the contract for platform-specific network measurement implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone
import time
import psutil

from app.schemas.network import NetworkInterfaceInfo, NetworkTelemetry
from app.collector.jitter import JitterCalculator


class BaseNetworkCollector(ABC):
    """Abstract base class for operating system specific network measurements."""

    def __init__(self, target_host: str = "8.8.8.8", ping_count: int = 5, ping_timeout: float = 2.0):
        self.target_host = target_host
        self.ping_count = ping_count
        self.ping_timeout = ping_timeout
        self.last_io_counters: Dict[str, Any] = {}
        self.last_timestamp: Optional[float] = None

    @abstractmethod
    def get_wifi_signal_strength(self, interface_name: str) -> Tuple[Optional[float], Optional[float]]:
        """Returns (signal_percentage, signal_dbm).
        
        Returns (None, None) if the interface is not Wi-Fi or RSSI is not exposed by OS.
        Never fabricates or invents a value.
        """
        pass

    @abstractmethod
    def ping_host(self, host: str, count: int, timeout_secs: float) -> Tuple[List[float], float]:
        """Pings target host.
        
        Returns:
            Tuple of (list_of_successful_rtt_delays_in_ms, packet_loss_percentage)
        """
        pass

    def get_all_interfaces(self) -> List[NetworkInterfaceInfo]:
        """Discovers all network interfaces and their current status."""
        interfaces_info = []
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        default_iface = self.get_default_interface_name()

        for name, stat in stats.items():
            ip_addresses = []
            if name in addrs:
                for addr in addrs[name]:
                    if addr.family.name in ("AF_INET", "AF_INET6"):
                        ip_addresses.append(addr.address)

            conn_type = self._classify_interface_type(name)
            info = NetworkInterfaceInfo(
                name=name,
                is_up=stat.isup,
                speed_mbps=float(stat.speed) if stat.speed > 0 else None,
                mtu=stat.mtu,
                addresses=ip_addresses,
                connection_type=conn_type,
                is_default=(name == default_iface)
            )
            interfaces_info.append(info)

        return interfaces_info

    def get_default_interface_name(self) -> Optional[str]:
        """Attempts to determine the active primary interface."""
        # Check active gateway or interface with active IP and traffic
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        io_counters = psutil.net_io_counters(pernic=True)

        candidate = None
        max_bytes = -1

        for name, stat in stats.items():
            if not stat.isup or "loopback" in name.lower():
                continue
            if name in addrs and any(a.family.name == "AF_INET" for a in addrs[name]):
                if name in io_counters:
                    traffic = io_counters[name].bytes_sent + io_counters[name].bytes_recv
                    if traffic > max_bytes:
                        max_bytes = traffic
                        candidate = name

        return candidate or (list(stats.keys())[0] if stats else None)

    def _classify_interface_type(self, interface_name: str) -> str:
        """Heuristically classifies interface type based on OS naming conventions."""
        name_lower = interface_name.lower()
        if "wi-fi" in name_lower or "wlan" in name_lower or "wireless" in name_lower or "wl" in name_lower:
            return "Wi-Fi"
        elif "ethernet" in name_lower or "eth" in name_lower or "en" in name_lower or "local area connection" in name_lower:
            return "Ethernet"
        elif "loopback" in name_lower or "lo" in name_lower:
            return "Loopback"
        elif "cellular" in name_lower or "mobile" in name_lower or "wwan" in name_lower:
            return "Cellular"
        elif "vethernet" in name_lower or "vbox" in name_lower or "vmnet" in name_lower:
            return "Virtual"
        return "Unknown"

    def collect_snapshot(self, interface_name: Optional[str] = None) -> NetworkTelemetry:
        """Performs a comprehensive telemetry measurement cycle."""
        target_iface = interface_name or self.get_default_interface_name() or "default"
        now_time = time.time()
        now_dt = datetime.now(timezone.utc)

        # 1. Measure Latency, Jitter, and Packet Loss
        rtt_samples, packet_loss = self.ping_host(
            self.target_host, self.ping_count, self.ping_timeout
        )

        if rtt_samples:
            avg_latency = float(sum(rtt_samples) / len(rtt_samples))
            min_latency = float(min(rtt_samples))
            max_latency = float(max(rtt_samples))
            mean_pdv_jitter = JitterCalculator.calculate_mean_pdv(rtt_samples)
            rfc_jitter = JitterCalculator.calculate_rfc3550_jitter(rtt_samples)
        else:
            # 100% packet loss / unreachable
            avg_latency = self.ping_timeout * 1000.0  # Cap at timeout ms
            min_latency = avg_latency
            max_latency = avg_latency
            mean_pdv_jitter = 0.0
            rfc_jitter = 0.0

        # 2. Wi-Fi Signal Strength
        signal_pct, signal_dbm = self.get_wifi_signal_strength(target_iface)
        conn_type = self._classify_interface_type(target_iface)

        # 3. Network I/O Counters & Rates
        pernic_io = psutil.net_io_counters(pernic=True)
        current_io = pernic_io.get(target_iface)
        if not current_io:
            total_io = psutil.net_io_counters()
            bytes_sent = total_io.bytes_sent
            bytes_recv = total_io.bytes_recv
            packets_sent = total_io.packets_sent
            packets_recv = total_io.packets_recv
        else:
            bytes_sent = current_io.bytes_sent
            bytes_recv = current_io.bytes_recv
            packets_sent = current_io.packets_sent
            packets_recv = current_io.packets_recv

        # Traffic Rate and Utilization calculation
        rate_bytes_sec = 0.0
        download_mbps = 0.0
        upload_mbps = 0.0
        utilization = 0.0

        if target_iface in self.last_io_counters and self.last_timestamp is not None:
            dt = now_time - self.last_timestamp
            if dt > 0.01:
                last_s, last_r = self.last_io_counters[target_iface]
                delta_sent = max(0, bytes_sent - last_s)
                delta_recv = max(0, bytes_recv - last_r)

                rate_bytes_sec = (delta_sent + delta_recv) / dt
                upload_mbps = round((delta_sent * 8.0) / (dt * 1_000_000.0), 3)
                download_mbps = round((delta_recv * 8.0) / (dt * 1_000_000.0), 3)

                # Link speed estimate for utilization
                stats = psutil.net_if_stats()
                iface_stat = stats.get(target_iface)
                link_speed_mbps = float(iface_stat.speed) if iface_stat and iface_stat.speed > 0 else 100.0
                total_mbps = download_mbps + upload_mbps
                utilization = min(100.0, round((total_mbps / link_speed_mbps) * 100.0, 2))

        self.last_io_counters[target_iface] = (bytes_sent, bytes_recv)
        self.last_timestamp = now_time

        traffic_kb_s = round(rate_bytes_sec / 1024.0, 2)
        traffic_mbps = round((rate_bytes_sec * 8.0) / 1_000_000.0, 3)

        return NetworkTelemetry(
            timestamp=now_dt,
            interface=target_iface,
            connection_type=conn_type,
            latency=round(avg_latency, 2),
            min_latency=round(min_latency, 2) if min_latency is not None else None,
            max_latency=round(max_latency, 2) if max_latency is not None else None,
            packet_loss=round(packet_loss, 2),
            jitter=round(mean_pdv_jitter, 2),
            rfc3550_jitter=round(rfc_jitter, 2),
            download_bandwidth=download_mbps,
            upload_bandwidth=upload_mbps,
            signal_strength=signal_pct,
            signal_strength_dbm=signal_dbm,
            bytes_sent=bytes_sent,
            bytes_received=bytes_recv,
            packets_sent=packets_sent,
            packets_received=packets_recv,
            traffic_rate=traffic_kb_s,
            traffic_rate_mbps=traffic_mbps,
            network_utilization=utilization
        )
