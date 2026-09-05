import heapq
import logging
import psutil
from dataclasses import dataclass
from typing import List, Tuple

logger = logging.getLogger("Processes")


@dataclass
class ProcessInfo:
    """
    Dataclass representing basic attributes of a running system process.
    """
    pid: int
    name: str
    cpu_percent: float
    memory_rss: int  # Resident Set Size (physical memory used) in bytes


class ProcessCollector:
    """
    Scans process tables and returns sorted processes targeting CPU and Memory consumption.
    """

    def __init__(self) -> None:
        """Initialize the Process Collector."""
        logger.info("Initializing Process Collector...")

    def collect(self) -> Tuple[List[ProcessInfo], List[ProcessInfo]]:
        """
        Scan system processes and partition them into top 10 CPU and top 10 Memory consumers.
        Uses lightweight tuples and heapq.nlargest to minimize allocations and CPU overhead.

        Returns:
            Tuple[List[ProcessInfo], List[ProcessInfo]]: (top_cpu_processes, top_memory_processes).
        """
        raw_pool: List[Tuple[int, str, float, int]] = []

        # Iterate over all active PIDs requesting only needed fields (huge speed improvement)
        for proc in psutil.process_iter(attrs=["pid", "name", "cpu_percent", "memory_info"]):
            try:
                info = proc.info
                pid = int(info["pid"])
                name = str(info["name"] or "Unknown")
                cpu_percent = float(info["cpu_percent"] or 0.0)

                mem_info = info["memory_info"]
                memory_rss = int(mem_info.rss) if mem_info else 0

                raw_pool.append((pid, name, cpu_percent, memory_rss))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Ignore short-lived or restricted system level processes
                continue
            except Exception as e:
                logger.debug("Error retrieving process info: %s", e)
                continue

        # Extract top 10 elements using heapq (O(N log K) instead of O(N log N))
        top_cpu_raw = heapq.nlargest(10, raw_pool, key=lambda p: p[2])
        top_mem_raw = heapq.nlargest(10, raw_pool, key=lambda p: p[3])

        # Construct dataclass instances only for the final 20 processes (saves huge RAM/CPU)
        top_cpu = [ProcessInfo(pid=p[0], name=p[1], cpu_percent=p[2], memory_rss=p[3]) for p in top_cpu_raw]
        top_mem = [ProcessInfo(pid=p[0], name=p[1], cpu_percent=p[2], memory_rss=p[3]) for p in top_mem_raw]

        return top_cpu, top_mem
