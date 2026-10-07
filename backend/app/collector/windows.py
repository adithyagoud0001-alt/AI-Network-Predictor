"""Windows Platform Network Telemetry Collector

Implements Windows-specific command execution and telemetry gathering
using netsh, native Windows ping.exe, and WMI/psutil bindings.
"""

import subprocess
import re
from typing import List, Tuple, Optional
import logging

from app.collector.base import BaseNetworkCollector

logger = logging.getLogger(__name__)


class WindowsNetworkCollector(BaseNetworkCollector):
    """Windows-specific network telemetry collector."""

    def ping_host(self, host: str, count: int, timeout_secs: float) -> Tuple[List[float], float]:
        """Executes native Windows ping command and parses individual packet RTTs."""
        timeout_ms = int(timeout_secs * 1000)
        cmd = ["ping", "-n", str(count), "-w", str(timeout_ms), host]

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
            logger.warning(f"Windows ping error or timeout: {exc}")
            return [], 100.0

        rtts: List[float] = []
        # Match lines like "Reply from 8.8.8.8: bytes=32 time=11ms TTL=116" or "time<1ms"
        for line in stdout.splitlines():
            line_str = line.strip()
            if "Reply from" in line_str or "Antwort von" in line_str:
                if "time<1ms" in line_str or "time<1 ms" in line_str:
                    rtts.append(0.5)
                else:
                    match = re.search(r"time[=<]\s*(\d+(\.\d+)?)\s*ms", line_str, re.IGNORECASE)
                    if match:
                        rtts.append(float(match.group(1)))

        # Parse loss percentage
        loss_pct = 100.0
        loss_match = re.search(r"\((\d+)%\s*(loss|Verlust)\)", stdout, re.IGNORECASE)
        if loss_match:
            loss_pct = float(loss_match.group(1))
        elif count > 0:
            loss_pct = float((count - len(rtts)) / count * 100.0)

        return rtts, max(0.0, min(100.0, loss_pct))

    def get_wifi_signal_strength(self, interface_name: str) -> Tuple[Optional[float], Optional[float]]:
        """Parses Windows netsh wlan show interfaces.
        
        Returns (signal_percentage, signal_dbm) or (None, None) if not Wi-Fi.
        """
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True,
                text=True,
                timeout=3.0,
                check=False
            )
            stdout = result.stdout
        except Exception as exc:
            logger.debug(f"Could not query netsh wlan: {exc}")
            return None, None

        if "There is no wireless interface" in stdout or "no interface" in stdout.lower():
            return None, None

        signal_match = re.search(r"Signal\s*:\s*(\d+)%", stdout)
        if signal_match:
            signal_pct = float(signal_match.group(1))
            # Standard heuristic formula for Wi-Fi signal percentage to dBm:
            # dBm ~= (signal_pct / 2) - 100 (where 100% is approx -50 dBm, 0% is approx -100 dBm)
            signal_dbm = round((signal_pct / 2.0) - 100.0, 1)
            return signal_pct, signal_dbm

        return None, None
