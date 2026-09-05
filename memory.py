"""
Memory metrics collection module for the Terminal System Dashboard Pro.
Monitors virtual memory (RAM) and swap memory allocation and usage.
"""

import logging
import psutil
from dataclasses import dataclass

logger = logging.getLogger("Memory")


@dataclass
class MemoryData:
    """
    Dataclass representing collected Memory metrics.
    """
    ram_total: int
    ram_used: int
    ram_available: int
    ram_percent: float
    swap_total: int
    swap_used: int
    swap_free: int
    swap_percent: float


class MemoryCollector:
    """
    Collects current usage statistics for physical memory (RAM) and virtual swap memory.
    """

    def __init__(self) -> None:
        """Initialize the Memory Collector."""
        logger.info("Initializing Memory Collector...")

    def collect(self) -> MemoryData:
        """
        Gather real-time memory usage statistics.

        Returns:
            MemoryData: The populated Memory metrics dataclass.
        """
        virtual_mem = psutil.virtual_memory()
        swap_mem = psutil.swap_memory()

        return MemoryData(
            ram_total=virtual_mem.total,
            ram_used=virtual_mem.used,
            ram_available=virtual_mem.available,
            ram_percent=float(virtual_mem.percent),
            swap_total=swap_mem.total,
            swap_used=swap_mem.used,
            swap_free=swap_mem.free,
            swap_percent=float(swap_mem.percent),
        )
