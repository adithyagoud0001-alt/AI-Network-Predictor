"""Linux Platform Network Telemetry Collector

Implements Linux-specific commands (ping -c, /proc/net/wireless, iwconfig, nmcli).
"""

import subprocess
import re
import os
from typing import List, Tuple, Optional
import logging

from app.collector.base import BaseNetworkCollector

logger = logging.getLogger(__name__)


class LinuxNetworkCollector(BaseNetworkCollector):
    """Linux-specific network telemetry collector."""

    def ping_host(self, host: str, count: int, timeout_secs: float) -> Tuple[List[float], float]:
        """Executes Linux ping command (-c count -W timeout)."""
        cmd = ["ping", "-c", str(count), "-W", str(int(timeout_secs)), host]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=(count * timeout_secs) + 3.0,
                check=False
            )
            stdout = result.stdout
        except (subprocess.TimeoutExpired, Exception) as exc:
            logger.warning(f"Linux ping error or timeout: {exc}")
            return [], 100.0

        rtts: List[float] = []
        for line in stdout.splitlines():
            # e.g., "64 bytes from 8.8.8.8: icmp_seq=1 ttl=116 time=14.2 ms"
            match = re.search(r"time=(\d+(\.\d+)?)\s*ms", line)
            if match:
                rtts.append(float(match.group(1)))

        loss_pct = 100.0
        # e.g. "5 packets transmitted, 5 received, 0% packet loss"
        loss_match = re.search(r"(\d+(\.\d+)?)%\s*packet loss", stdout)
        if loss_match:
            loss_pct = float(loss_match.group(1))
        elif count > 0:
            loss_pct = float((count - len(rtts)) / count * 100.0)

        return rtts, max(0.0, min(100.0, loss_pct))

    def get_wifi_signal_strength(self, interface_name: str) -> Tuple[Optional[float], Optional[float]]:
        """Reads signal strength from /proc/net/wireless or iwconfig."""
        # 1. Try /proc/net/wireless
        if os.path.exists("/proc/net/wireless"):
            try:
                with open("/proc/net/wireless", "r") as f:
                    lines = f.readlines()
                for line in lines[2:]:
                    parts = line.split()
                    if parts and interface_name in parts[0]:
                        # Quality level is typically parts[2]
                        link_qual = float(parts[2].replace(".", ""))
                        pct = min(100.0, max(0.0, (link_qual / 70.0) * 100.0))
                        dbm = float(parts[3].replace(".", "")) if len(parts) > 3 else (pct / 2.0 - 100.0)
                        return round(pct, 1), round(dbm, 1)
            except Exception as exc:
                logger.debug(f"Error reading /proc/net/wireless: {exc}")

        # 2. Try iwconfig
        try:
            result = subprocess.run(["iwconfig", interface_name], capture_output=True, text=True, timeout=2.0)
            stdout = result.stdout
            qual_match = re.search(r"Link Quality=(\d+)/(\d+)", stdout)
            sig_match = re.search(r"Signal level=(-\d+|\d+)\s*dBm", stdout)
            if qual_match:
                cur = float(qual_match.group(1))
                max_q = float(qual_match.group(2))
                pct = round((cur / max_q) * 100.0, 1)
                dbm = float(sig_match.group(1)) if sig_match else round((pct / 2.0) - 100.0, 1)
                return pct, dbm
        except Exception:
            pass

        return None, None
