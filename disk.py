"""
Disk space and I/O metrics collection module for the Terminal System Dashboard Pro.
Monitors filesystem usage, partition status, and disk read/write throughput.
"""

import time
import logging
import psutil
from dataclasses import dataclass
from typing import List

logger = logging.getLogger("Disk")


@dataclass
class DiskPartitionData:
    """
    Dataclass representing metrics for a single disk partition.
    """
    device: str
    mountpoint: str
    fstype: str
    total: int
    used: int
    free: int
    percent: float


@dataclass
class DiskData:
    """
    Dataclass representing unified disk performance and capacity metrics.
    """
    partitions: List[DiskPartitionData]
    read_speed: float  # Bytes per second
    write_speed: float  # Bytes per second


class DiskCollector:
    """
    Collects storage space levels across mount points and calculates physical drive read/write bandwidth.
    """

    def __init__(self) -> None:
        """Initialize parameters for tracking disk bandwidth over time."""
        logger.info("Initializing Disk Collector...")
        self._prev_io = self._get_io_counters()
        self._prev_time: float = time.time()

    def _get_io_counters(self) -> getattr(psutil, "disk_io_counters", None):
        """Safely fetch global disk I/O counters, catching OS level warnings or issues."""
        try:
            return psutil.disk_io_counters()
        except Exception as e:
            logger.debug("Failed to retrieve disk IO counters: %s", e)
            return None

    def collect(self) -> DiskData:
        """
        Gather real-time storage capacities and active read/write disk speeds.

        Returns:
            DiskData: The populated Disk metrics dataclass.
        """
        partitions_list: List[DiskPartitionData] = []
        
        # Gather all physical mount points (all=False skips system loops/ramdisks)
        try:
            partitions = psutil.disk_partitions(all=False)
        except Exception as e:
            logger.error("Could not read disk partitions: %s", e)
            partitions = []

        for part in partitions:
            # Skip read-only CD-ROMs or unmounted nodes
            if not part.fstype or "loop" in part.device:
                continue

            # Skip macOS system internal volumes and translocation paths
            mount = part.mountpoint
            ignored_prefixes = (
                "/System/Volumes/VM",
                "/System/Volumes/Preboot",
                "/System/Volumes/Update",
                "/System/Volumes/xarts",
                "/System/Volumes/iSCPreboot",
                "/System/Volumes/Hardware",
                "/private/var/folders",
            )
            if any(mount.startswith(p) for p in ignored_prefixes) or "AppTranslocation" in mount:
                continue

            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions_list.append(
                    DiskPartitionData(
                        device=part.device,
                        mountpoint=part.mountpoint,
                        fstype=part.fstype,
                        total=usage.total,
                        used=usage.used,
                        free=usage.free,
                        percent=float(usage.percent),
                    )
                )
            except (PermissionError, FileNotFoundError):
                # Happens for system recovery blocks or locked directories
                continue
            except Exception as e:
                logger.debug("Failed reading usage for partition %s: %s", part.mountpoint, e)
                continue

        # Bandwidth calculation
        current_io = self._get_io_counters()
        current_time = time.time()

        read_speed = 0.0
        write_speed = 0.0

        if self._prev_io and current_io:
            time_delta = current_time - self._prev_time
            if time_delta > 0.05:  # Ensure a minimum measurement window
                try:
                    read_diff = current_io.read_bytes - self._prev_io.read_bytes
                    write_diff = current_io.write_bytes - self._prev_io.write_bytes
                    
                    read_speed = max(0.0, float(read_diff / time_delta))
                    write_speed = max(0.0, float(write_diff / time_delta))
                except (AttributeError, TypeError) as e:
                    logger.debug("Error computing IO speed: %s", e)

        # Update tracking window
        self._prev_io = current_io
        self._prev_time = current_time

        return DiskData(
            partitions=partitions_list,
            read_speed=read_speed,
            write_speed=write_speed,
        )
