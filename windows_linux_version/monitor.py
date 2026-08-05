"""
Unified monitoring coordinator for the Terminal System Dashboard Pro.
Aggregates platform diagnostics and individual system statistics into a single state.
"""

import os
import sys
import platform
import time
import getpass
import logging
import psutil
from dataclasses import dataclass
from typing import List, Tuple

from cpu import CPUCollector, CPUData
from memory import MemoryCollector, MemoryData
from disk import DiskCollector, DiskData
from network import NetworkCollector, NetworkData
from battery import BatteryCollector, BatteryData
from processes import ProcessCollector, ProcessInfo
from utils import uptime, safe_execute

logger = logging.getLogger("Monitor")


@dataclass
class OSData:
    """
    Dataclass containing system operating system parameters and uptime metrics.
    """
    system: str
    release: str
    version: str
    machine: str
    processor: str
    boot_time: float
    uptime_str: str
    username: str
    python_version: str


@dataclass
class SystemState:
    """
    Unified container containing complete snapshots of system health metrics.
    """
    os: OSData
    cpu: CPUData
    memory: MemoryData
    disk: DiskData
    network: NetworkData
    battery: BatteryData
    top_cpu_processes: List[ProcessInfo]
    top_mem_processes: List[ProcessInfo]
    timestamp: float


class SystemMonitor:
    """
    Coordinates metrics gatherers and produces composite SystemState reports.
    """

    def __init__(self) -> None:
        """Instantiate collectors and discover static runtime properties."""
        logger.info("Initializing System Monitor Orchestrator...")
        
        # Instantiate child subsystem collectors
        self.cpu_collector = CPUCollector()
        self.memory_collector = MemoryCollector()
        self.disk_collector = DiskCollector()
        self.network_collector = NetworkCollector()
        self.battery_collector = BatteryCollector()
        self.process_collector = ProcessCollector()

        # Discover and cache operating system info
        try:
            self._boot_time: float = psutil.boot_time()
        except Exception:
            self._boot_time = time.time()  # Fallback to launch time on error

        self._username: str = self._fetch_username()
        self._python_version: str = platform.python_version()
        self._system: str = platform.system()
        self._release: str = platform.release()
        self._version: str = platform.version()
        self._machine: str = platform.machine()
        self._processor: str = platform.processor() or "Unknown"

    @safe_execute("Unknown User")
    def _fetch_username(self) -> str:
        """Find local user account name."""
        return getpass.getuser()

    def collect(self) -> SystemState:
        """
        Query all collectors synchronously to build a unified system status report.

        Returns:
            SystemState: An immutable dataclass containing complete metrics.
        """
        os_data = OSData(
            system=self._system,
            release=self._release,
            version=self._version,
            machine=self._machine,
            processor=self._processor,
            boot_time=self._boot_time,
            uptime_str=uptime(self._boot_time),
            username=self._username,
            python_version=self._python_version,
        )

        top_cpu_proc, top_mem_proc = self.process_collector.collect()

        return SystemState(
            os=os_data,
            cpu=self.cpu_collector.collect(),
            memory=self.memory_collector.collect(),
            disk=self.disk_collector.collect(),
            network=self.network_collector.collect(),
            battery=self.battery_collector.collect(),
            top_cpu_processes=top_cpu_proc,
            top_mem_processes=top_mem_proc,
            timestamp=time.time(),
        )
