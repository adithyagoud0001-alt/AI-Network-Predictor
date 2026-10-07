"""macOS Platform Network Telemetry Collector

Implements macOS-specific ping and airport utility parsing.
"""

import subprocess
import re
import os
from typing import List, Tuple, Optional
import logging

from app.collector.base import BaseNetworkCollector

logger = logging.getLogger(__name__)


class MacOSNetworkCollector(BaseNetworkCollector):
    """macOS-specific network telemetry collector."""

    def ping_host(self, host: str, count: int, timeout_secs: float) -> Tuple[List[float], float]:
        """Executes macOS ping command (-c count -W timeout_ms)."""
        timeout_ms = int(timeout_secs * 1000)
        cmd = ["ping", "-c", str(count), "-W", str(timeout_ms), host]

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
            logger.warning(f"macOS ping error or timeout: {exc}")
            return [], 100.0

        rtts: List[float] = []
        for line in stdout.splitlines():
            match = re.search(r"time=(\d+(\.\d+)?)\s*ms", line)
            if match:
                rtts.append(float(match.group(1)))

        loss_pct = 100.0
        loss_match = re.search(r"(\d+(\.\d+)?)%\s*packet loss", stdout)
        if loss_match:
            loss_pct = float(loss_match.group(1))
        elif count > 0:
            loss_pct = float((count - len(rtts)) / count * 100.0)

        return rtts, max(0.0, min(100.0, loss_pct))

    def get_wifi_signal_strength(self, interface_name: str) -> Tuple[Optional[float], Optional[float]]:
        """Parses macOS airport utility for Wi-Fi RSSI."""
        airport_bin = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        if not os.path.exists(airport_bin):
            return None, None

        try:
            result = subprocess.run([airport_bin, "-I"], capture_output=True, text=True, timeout=2.0)
            stdout = result.stdout
            agr_match = re.search(r"agrCtlRSSI:\s*(-\d+)", stdout)
            if agr_match:
                rssi = float(agr_match.group(1))
                # Map -100 dBm (0%) to -50 dBm (100%)
                pct = max(0.0, min(100.0, (rssi + 100.0) * 2.0))
                return round(pct, 1), rssi
        except Exception:
            pass

        return None, None
