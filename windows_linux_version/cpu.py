"""
CPU metrics collection module for the Terminal System Dashboard Pro (Windows & Linux).
Retrieves processor information, core counts, usage per core, clock frequency,
temperatures, power usage (RAPL on Linux), and NVIDIA GPU metrics via GPUtil.
"""

import os
import sys
import logging
import subprocess
import platform
import time
import psutil
from dataclasses import dataclass
from typing import List, Optional, Dict
from utils import safe_execute

logger = logging.getLogger("CPU")


@dataclass
class CPUData:
    model: str
    architecture: str
    physical_cores: int
    logical_cores: int
    usage_overall: float
    usage_per_core: List[float]
    frequency_current: float
    frequency_max: float
    temperature: Optional[float]          # CPU temp
    cpu_power_w: Optional[float]          # RAPL on Linux
    thermal_pressure: str                 # N/A on Win/Linux
    # GPU (NVIDIA via GPUtil)
    gpu_name: Optional[str]
    gpu_temp: Optional[float]
    gpu_load: Optional[float]
    gpu_memory_used: Optional[float]      # MB
    gpu_memory_total: Optional[float]     # MB
    gpu_power_w: Optional[float]


class CPUCollector:
    """
    Orchestrates gathering of CPU and GPU specifications and utilization metrics
    for Windows and Linux platforms.
    Static parameters are cached upon instantiation to optimize execution speed.
    """

    def __init__(self) -> None:
        """Initialize and cache static processor identifiers and set baselines."""
        logger.info("Initializing CPU Collector...")
        self._model: str = self._fetch_cpu_model()
        self._architecture: str = self._fetch_cpu_arch()
        self._physical_cores: int = psutil.cpu_count(logical=False) or 0
        self._logical_cores: int = psutil.cpu_count(logical=True) or 0

        # RAPL state tracking for non-blocking power calculation (Linux only)
        self._last_rapl_energy: Optional[float] = None
        self._last_rapl_time: Optional[float] = None
        if sys.platform == "linux":
            try:
                # Perform an initial read to establish baseline
                energy = self._read_rapl_energy()
                if energy is not None:
                    self._last_rapl_energy = energy
                    self._last_rapl_time = time.time()
            except Exception as e:
                logger.debug("Failed to initialize RAPL baseline: %s", e)

        # Initialize psutil percent collection baseline
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None, percpu=True)

    @safe_execute("Unknown Processor")
    def _fetch_cpu_model(self) -> str:
        """Fetch marketing brand name of CPU."""
        if sys.platform == "linux":
            try:
                with open("/proc/cpuinfo") as f:
                    for line in f:
                        if "model name" in line.lower():
                            return line.split(":")[-1].strip()
            except Exception:
                pass
        elif sys.platform == "win32":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                model, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                winreg.CloseKey(key)
                if model and model.strip():
                    return model.strip()
            except Exception:
                pass

        # Lazy fallback
        try:
            import cpuinfo
            info = cpuinfo.get_cpu_info()
            return str(info.get("brand_raw", "Unknown Processor"))
        except ImportError:
            return "Unknown Processor"

    @safe_execute("Unknown Arch")
    def _fetch_cpu_arch(self) -> str:
        """Fetch architecture classification (e.g. X86_64, ARM_8)."""
        arch = platform.machine()
        if arch:
            if arch.lower() == "arm64":
                return "ARM_8"
            return arch

        # Lazy fallback
        try:
            import cpuinfo
            info = cpuinfo.get_cpu_info()
            return str(info.get("arch", "Unknown Arch"))
        except ImportError:
            return "Unknown Arch"

    @safe_execute(None)
    def _fetch_cpu_temp(self) -> Optional[float]:
        """
        Query system temperature sensors using psutil (Linux/Windows) or WMI (Windows).
        Returns:
            Optional[float]: Temperature in Celsius if sensors exist, else None.
        """
        if hasattr(psutil, "sensors_temperatures"):
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    sensor_keys = ["coretemp", "cpu_thermal", "k10temp", "acpitz"]
                    for key in sensor_keys:
                        if key in temps and temps[key]:
                            return float(temps[key][0].current)
                    for sensor_list in temps.values():
                        if sensor_list:
                            return float(sensor_list[0].current)
            except Exception as e:
                logger.debug("Failed to read temps via psutil: %s", e)

        # Windows WMI fallback
        if sys.platform == "win32":
            try:
                result = subprocess.run(
                    ["wmic", "/namespace:\\\\root\\wmi", "PATH", "MSAcpi_ThermalZoneTemperature", "get", "CurrentTemperature"],
                    capture_output=True, text=True, timeout=3
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    if len(lines) >= 2:
                        # Value is in decikelvins
                        decikelvins = float(lines[1].strip())
                        celsius = (decikelvins / 10.0) - 273.15
                        return round(celsius, 1)
            except Exception as e:
                logger.debug("Failed to read WMI temp: %s", e)

        return None

    def _read_rapl_energy(self) -> Optional[float]:
        """Helper to read energy_uj from intel-rapl on Linux."""
        try:
            with open("/sys/class/powercap/intel-rapl:0/energy_uj", "r") as f:
                return float(f.read().strip())
        except Exception:
            return None

    @safe_execute(None)
    def _fetch_cpu_power_rapl(self) -> Optional[float]:
        """
        On Linux only, computes CPU power in Watts based on intel-rapl energy_uj.
        Uses cached previous reading to avoid blocking.
        """
        if sys.platform != "linux":
            return None
        
        current_energy = self._read_rapl_energy()
        current_time = time.time()
        
        if current_energy is None:
            return None
            
        power_w = None
        if self._last_rapl_energy is not None and self._last_rapl_time is not None:
            energy_diff = current_energy - self._last_rapl_energy
            time_diff = current_time - self._last_rapl_time
            
            # Handle counter wrap-around
            if energy_diff < 0:
                energy_diff += 2**64
                
            if time_diff > 0:
                power_w = (energy_diff / 1_000_000.0) / time_diff
                
        self._last_rapl_energy = current_energy
        self._last_rapl_time = current_time
        
        return power_w

    @safe_execute("N/A")
    def _fetch_thermal_pressure(self) -> str:
        """
        No direct equivalent on Win/Linux in this context.
        Always returns 'N/A'.
        """
        return "N/A"
        
    @safe_execute({})
    def _fetch_gpu_info(self) -> Dict:
        """
        Uses GPUtil to detect NVIDIA GPUs. Returns dict with metrics.
        Attempts to get power draw via nvidia-smi.
        """
        gpu_info = {}
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_info["gpu_name"] = gpu.name
                gpu_info["gpu_temp"] = float(gpu.temperature)
                gpu_info["gpu_load"] = float(gpu.load * 100.0) # GPUtil load is 0.0-1.0
                gpu_info["gpu_memory_used"] = float(gpu.memoryUsed)
                gpu_info["gpu_memory_total"] = float(gpu.memoryTotal)
                
                # Power draw via nvidia-smi
                try:
                    result = subprocess.run(
                        ["nvidia-smi", "--query-gpu=power.draw", "--format=csv,noheader,nounits"],
                        capture_output=True, text=True, timeout=2
                    )
                    if result.returncode == 0:
                        val = result.stdout.strip()
                        if val and "ERR!" not in val and "[Not Supported]" not in val:
                            gpu_info["gpu_power_w"] = float(val)
                except Exception as e:
                    logger.debug("Failed to read GPU power via nvidia-smi: %s", e)
        except ImportError:
            logger.debug("GPUtil not installed, skipping GPU metrics.")
        except Exception as e:
            logger.debug("Error fetching GPU info: %s", e)
            
        return gpu_info

    def collect(self) -> CPUData:
        """
        Gather real-time CPU and GPU performance statistics.

        Returns:
            CPUData: The populated CPU metrics dataclass.
        """
        # interval=None enables immediate non-blocking return utilizing previous step duration
        usage_overall = float(psutil.cpu_percent(interval=None))
        usage_per_core = [float(val) for val in psutil.cpu_percent(interval=None, percpu=True)]

        freq_info = psutil.cpu_freq()
        freq_current = float(freq_info.current) if freq_info else 0.0
        freq_max = float(freq_info.max) if freq_info else 0.0

        temp = self._fetch_cpu_temp()
        power_w = self._fetch_cpu_power_rapl()
        thermal = self._fetch_thermal_pressure()
        
        gpu_info = self._fetch_gpu_info()

        return CPUData(
            model=self._model,
            architecture=self._architecture,
            physical_cores=self._physical_cores,
            logical_cores=self._logical_cores,
            usage_overall=usage_overall,
            usage_per_core=usage_per_core,
            frequency_current=freq_current,
            frequency_max=freq_max,
            temperature=temp,
            cpu_power_w=power_w,
            thermal_pressure=thermal,
            gpu_name=gpu_info.get("gpu_name"),
            gpu_temp=gpu_info.get("gpu_temp"),
            gpu_load=gpu_info.get("gpu_load"),
            gpu_memory_used=gpu_info.get("gpu_memory_used"),
            gpu_memory_total=gpu_info.get("gpu_memory_total"),
            gpu_power_w=gpu_info.get("gpu_power_w"),
        )
