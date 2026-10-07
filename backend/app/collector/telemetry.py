"""Unified Network Telemetry Collector Service

Provides the cross-platform factory and background collection engine.
"""

import sys
import time
import asyncio
import logging
from collections import deque
from typing import Optional, List, Callable, Dict, Any

from app.schemas.network import NetworkTelemetry, NetworkInterfaceInfo, CollectorStatus
from app.collector.base import BaseNetworkCollector
from app.collector.windows import WindowsNetworkCollector
from app.collector.linux import LinuxNetworkCollector
from app.collector.macos import MacOSNetworkCollector
from app.config import settings

logger = logging.getLogger(__name__)


def create_platform_collector(
    target_host: Optional[str] = None,
    ping_count: Optional[int] = None,
    ping_timeout: Optional[float] = None
) -> BaseNetworkCollector:
    """Factory function instantiating the OS-appropriate network collector."""
    host = target_host or settings.DEFAULT_PING_TARGET
    count = ping_count or settings.PING_COUNT
    timeout = ping_timeout or settings.PING_TIMEOUT_SECONDS

    plat = sys.platform.lower()
    if plat.startswith("win"):
        logger.info(f"Instantiating WindowsNetworkCollector (target={host})")
        return WindowsNetworkCollector(target_host=host, ping_count=count, ping_timeout=timeout)
    elif plat.startswith("linux"):
        logger.info(f"Instantiating LinuxNetworkCollector (target={host})")
        return LinuxNetworkCollector(target_host=host, ping_count=count, ping_timeout=timeout)
    elif plat.startswith("darwin"):
        logger.info(f"Instantiating MacOSNetworkCollector (target={host})")
        return MacOSNetworkCollector(target_host=host, ping_count=count, ping_timeout=timeout)
    else:
        logger.warning(f"Unrecognized platform '{plat}', falling back to LinuxNetworkCollector")
        return LinuxNetworkCollector(target_host=host, ping_count=count, ping_timeout=timeout)


class NetworkTelemetryService:
    """Manages periodic telemetry sampling, history buffers, and callbacks."""

    def __init__(
        self,
        collector: Optional[BaseNetworkCollector] = None,
        interval_seconds: Optional[float] = None,
        max_history_size: int = 500
    ):
        self.collector = collector or create_platform_collector()
        self.interval = interval_seconds or settings.COLLECTOR_INTERVAL_SECONDS
        self.max_history_size = max_history_size
        self.history: deque[NetworkTelemetry] = deque(maxlen=max_history_size)
        self.subscribers: List[Callable[[NetworkTelemetry], Any]] = []

        self._task: Optional[asyncio.Task] = None
        self._is_running: bool = False
        self._selected_interface: Optional[str] = None
        self._total_collected: int = 0

    @property
    def is_running(self) -> bool:
        return self._is_running

    def set_interface(self, interface_name: Optional[str]) -> None:
        """Select a specific network interface or None for auto-detect."""
        self._selected_interface = interface_name
        logger.info(f"Telemetry interface set to: {interface_name or 'Auto-detected default'}")

    def get_status(self) -> CollectorStatus:
        latest = self.history[-1] if self.history else None
        return CollectorStatus(
            is_running=self._is_running,
            active_interface=self._selected_interface or (latest.interface if latest else None),
            target_host=self.collector.target_host,
            interval_seconds=self.interval,
            total_samples_collected=self._total_collected,
            last_collection_time=latest.timestamp if latest else None
        )

    def get_interfaces(self) -> List[NetworkInterfaceInfo]:
        return self.collector.get_all_interfaces()

    def get_latest_telemetry(self) -> Optional[NetworkTelemetry]:
        return self.history[-1] if self.history else None

    def get_telemetry_history(self, limit: int = 50) -> List[NetworkTelemetry]:
        all_items = list(self.history)
        return all_items[-limit:]

    def add_subscriber(self, callback: Callable[[NetworkTelemetry], Any]) -> None:
        if callback not in self.subscribers:
            self.subscribers.append(callback)

    def remove_subscriber(self, callback: Callable[[NetworkTelemetry], Any]) -> None:
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    def collect_now(self) -> NetworkTelemetry:
        """Runs a synchronous snapshot immediately."""
        telemetry = self.collector.collect_snapshot(self._selected_interface)
        self.history.append(telemetry)
        self._total_collected += 1
        self._notify_subscribers(telemetry)
        return telemetry

    def _notify_subscribers(self, telemetry: NetworkTelemetry) -> None:
        for cb in self.subscribers:
            try:
                res = cb(telemetry)
                if asyncio.iscoroutine(res):
                    asyncio.create_task(res)
            except Exception as exc:
                logger.error(f"Error in telemetry subscriber callback: {exc}")

    async def _collection_loop(self) -> None:
        logger.info(f"Starting network telemetry collection loop (interval={self.interval}s)")
        loop = asyncio.get_running_loop()
        while self._is_running:
            start_t = time.time()
            try:
                # Run the blocking collector snapshot in executor thread to prevent blocking event loop
                telemetry = await loop.run_in_executor(
                    None,
                    self.collector.collect_snapshot,
                    self._selected_interface
                )
                self.history.append(telemetry)
                self._total_collected += 1
                self._notify_subscribers(telemetry)
            except Exception as exc:
                logger.error(f"Telemetry collection cycle error: {exc}", exc_info=True)

            elapsed = time.time() - start_t
            sleep_time = max(0.5, self.interval - elapsed)
            try:
                await asyncio.sleep(sleep_time)
            except asyncio.CancelledError:
                break

    def start(self) -> None:
        if not self._is_running:
            self._is_running = True
            self._task = asyncio.create_task(self._collection_loop())
            logger.info("NetworkTelemetryService background task started")

    async def stop(self) -> None:
        if self._is_running:
            self._is_running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
                self._task = None
            logger.info("NetworkTelemetryService background task stopped")


telemetry_service = NetworkTelemetryService()
