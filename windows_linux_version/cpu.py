"""
CPU metrics collection module for the Terminal System Dashboard Pro.
Retrieves processor information, core counts (P/E), GPU/NPU cores,
usage per core, clock frequency, die/hotspot temperatures, power usage, and thermal pressure.

On Apple Silicon Macs with sudo access, reads CPU die temperature,
GPU die temperature, and computes the hotspot (max sensor) using
powermetrics. Requires sudo credentials to be cached before the
dashboard starts.
"""

import os
import sys
import re
import logging
import subprocess
import platform
import threading
import time
import psutil
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
from utils import safe_execute

logger = logging.getLogger("CPU")


@dataclass
class CPUData:
    """
    Dataclass representing collected CPU metrics.
    """
    model: str
    architecture: str
    physical_cores: int
    logical_cores: int
    performance_cores: Optional[int]
    efficiency_cores: Optional[int]
    gpu_cores: Optional[int]
    npu_cores: Optional[int]
    usage_overall: float
    usage_per_core: List[float]
    frequency_current: float
    frequency_max: float
    temperature: Optional[float]
    cpu_die_temp: Optional[float]
    gpu_die_temp: Optional[float]
    hotspot_temp: Optional[float]
    cpu_power_w: Optional[float]
    gpu_power_w: Optional[float]
    thermal_pressure: str


class CPUCollector:
    """
    Orchestrates gathering of CPU specifications and utilization metrics.
    Static parameters are cached upon instantiation to optimize execution speed.
    On Apple Silicon Macs, queries sysctl and system_profiler for P/E core
    breakdowns, GPU core count, and Neural Engine core count.
    When sudo access is available, spawns a background thread to periodically
    read die-level temperatures and power usage via powermetrics.
    """

    def __init__(self) -> None:
        """Initialize and cache static processor identifiers and set baselines."""
        logger.info("Initializing CPU Collector...")
        self._model: str = self._fetch_cpu_model()
        self._architecture: str = self._fetch_cpu_arch()
        self._physical_cores: int = psutil.cpu_count(logical=False) or 0
        self._logical_cores: int = psutil.cpu_count(logical=True) or 0
        self._is_apple_silicon: bool = self._detect_apple_silicon()

        # Apple Silicon specific data (cached at startup — these don't change)
        self._perf_cores: Optional[int] = None
        self._eff_cores: Optional[int] = None
        self._gpu_cores: Optional[int] = None
        self._npu_cores: Optional[int] = None

        if self._is_apple_silicon:
            self._perf_cores, self._eff_cores = self._fetch_pe_cores()
            self._gpu_cores = self._fetch_gpu_cores()
            self._npu_cores = self._fetch_npu_cores()

        # Die-level temperature readings and power (updated by background thread)
        self._cpu_die_temp: Optional[float] = None
        self._gpu_die_temp: Optional[float] = None
        self._hotspot_temp: Optional[float] = None
        self._cpu_power_w: Optional[float] = None
        self._gpu_power_w: Optional[float] = None
        
        self._sudo_available: bool = False
        self._temp_thread_running: bool = False

        # Check if sudo credentials are cached and start background temp reader
        if self._is_apple_silicon:
            self._sudo_available = self._check_sudo_cached()
            if self._sudo_available:
                self._start_temp_reader()

        # Initialize psutil percent collection baseline
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None, percpu=True)

    def _detect_apple_silicon(self) -> bool:
        """Check if we are running on an Apple Silicon Mac."""
        if sys.platform != "darwin":
            return False
        return platform.machine() == "arm64" and "Apple" in self._model

    def _check_sudo_cached(self) -> bool:
        """
        Check if sudo credentials are currently cached (no password prompt needed).

        Returns:
            bool: True if sudo can run without a password prompt right now.
        """
        try:
            result = subprocess.run(
                ["sudo", "-n", "true"],
                capture_output=True, timeout=3
            )
            return result.returncode == 0
        except Exception:
            return False

    @safe_execute("Unknown Processor")
    def _fetch_cpu_model(self) -> str:
        """Fetch marketing brand name of CPU."""
        if sys.platform == "darwin":
            try:
                res = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, timeout=2)
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout.strip()
            except Exception:
                pass
        elif sys.platform == "linux":
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
        import cpuinfo
        info = cpuinfo.get_cpu_info()
        return str(info.get("brand_raw", "Unknown Processor"))

    @safe_execute("Unknown Arch")
    def _fetch_cpu_arch(self) -> str:
        """Fetch architecture classification (e.g. X86_64, ARM_8)."""
        arch = platform.machine()
        if arch:
            if arch.lower() == "arm64":
                return "ARM_8"
            return arch

        # Lazy fallback
        import cpuinfo
        info = cpuinfo.get_cpu_info()
        return str(info.get("arch", "Unknown Arch"))

    @safe_execute((None, None))
    def _fetch_pe_cores(self) -> Tuple[Optional[int], Optional[int]]:
        """
        Query sysctl for Performance and Efficiency core counts on Apple Silicon.

        Returns:
            Tuple of (performance_cores, efficiency_cores) or (None, None) if unavailable.
        """
        perf_cores = None
        eff_cores = None

        try:
            result = subprocess.run(
                ["sysctl", "hw.perflevel0.physicalcpu", "hw.perflevel1.physicalcpu"],
                capture_output=True, text=True, timeout=3
            )
            for line in result.stdout.strip().splitlines():
                if "perflevel0.physicalcpu:" in line:
                    perf_cores = int(line.split(":")[-1].strip())
                elif "perflevel1.physicalcpu:" in line:
                    eff_cores = int(line.split(":")[-1].strip())
        except Exception as e:
            logger.debug("Failed to query P/E cores via sysctl: %s", e)

        return perf_cores, eff_cores

    @safe_execute(None)
    def _fetch_gpu_cores(self) -> Optional[int]:
        """
        Query system_profiler for GPU core count on Apple Silicon.

        Returns:
            Optional[int]: Number of GPU cores, or None if unavailable.
        """
        try:
            import plistlib
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType", "-xml"],
                capture_output=True, timeout=5
            )
            plist = plistlib.loads(result.stdout)
            items = plist[0]["_items"][0]
            cores = items.get("sppci_cores")
            if cores is not None:
                return int(cores)
        except Exception as e:
            logger.debug("Failed to query GPU cores: %s", e)
        return None

    @safe_execute(None)
    def _fetch_npu_cores(self) -> Optional[int]:
        """
        Determine Neural Engine core count for known Apple Silicon chips.

        Apple does not expose NPU core count via a simple API, so we match
        based on the chip model name. If unknown, returns None.

        Returns:
            Optional[int]: Number of Neural Engine cores.
        """
        # Known Neural Engine core counts for Apple Silicon chips
        npu_map = {
            "M1": 16, "M1 Pro": 16, "M1 Max": 16, "M1 Ultra": 32,
            "M2": 16, "M2 Pro": 16, "M2 Max": 16, "M2 Ultra": 32,
            "M3": 16, "M3 Pro": 16, "M3 Max": 16, "M3 Ultra": 32,
            "M4": 16, "M4 Pro": 16, "M4 Max": 16, "M4 Ultra": 32,
            "M5": 16, "M5 Pro": 16, "M5 Max": 16, "M5 Ultra": 32,
        }

        model_upper = self._model.upper()
        # Walk from longest chip name to shortest to match "M2 Ultra" before "M2"
        for chip_name in sorted(npu_map.keys(), key=len, reverse=True):
            if chip_name.upper() in model_upper:
                return npu_map[chip_name]

        return None

    # ------------------------------------------------------------------
    # Die-level temperature and power reading via sudo powermetrics
    # ------------------------------------------------------------------

    def _start_temp_reader(self) -> None:
        """Spawn a daemon thread that periodically reads die temperatures."""
        if self._temp_thread_running:
            return
        self._temp_thread_running = True
        thread = threading.Thread(target=self._temp_reader_loop, daemon=True)
        thread.start()
        logger.info("Started background die-temperature reader thread.")

    def _temp_reader_loop(self) -> None:
        """
        Background loop that runs sudo powermetrics every ~3 seconds to fetch
        die-level thermal data. Parses text output for temperature lines.
        """
        while self._temp_thread_running:
            try:
                result = subprocess.run(
                    [
                        "sudo", "-n", "powermetrics",
                        "--samplers", "cpu_power,gpu_power,thermal",
                        "-i", "200",      # 200 ms sample interval to guarantee sensor updates
                        "-n", "1",      # one sample only
                    ],
                    capture_output=True, text=True, timeout=10,
                )

                if result.returncode != 0:
                    # Sudo credentials likely expired
                    logger.warning("powermetrics returned non-zero; sudo may have expired.")
                    self._sudo_available = False
                    self._temp_thread_running = False
                    break

                self._parse_powermetrics_output(result.stdout)

            except subprocess.TimeoutExpired:
                logger.debug("powermetrics timed out.")
            except Exception as e:
                logger.debug("Error in temp reader: %s", e)

            # Wait before next reading — powermetrics is expensive
            time.sleep(3.0)

    def _parse_powermetrics_output(self, output: str) -> None:
        """
        Parse the text-format powermetrics output for temperature and power readings.
        """
        all_temps: List[float] = []
        cpu_die = None
        gpu_die = None
        cpu_power = None
        gpu_power = None

        for line in output.splitlines():
            stripped = line.strip()
            lower = stripped.lower()

            # 1. Parse temperature sensors
            if "temperature" in lower:
                try:
                    # Robust match for digits followed by optional spaces and C
                    match = re.search(r'([0-9.]+)\s*[Cc]', stripped)
                    if match:
                        temp_val = float(match.group(1))
                        all_temps.append(temp_val)

                        if "cpu die" in lower or "cpu active" in lower:
                            cpu_die = temp_val
                        elif "gpu die" in lower or "gpu active" in lower:
                            gpu_die = temp_val
                except Exception:
                    pass

            # 2. Parse power consumption
            if "cpu power" in lower:
                try:
                    match = re.search(r'cpu power:\s*([0-9.]+)\s*(\w+)', lower)
                    if match:
                        val = float(match.group(1))
                        unit = match.group(2)
                        cpu_power = val / 1000.0 if unit == "mw" else val
                except Exception:
                    pass
            elif "gpu power" in lower:
                try:
                    match = re.search(r'gpu power:\s*([0-9.]+)\s*(\w+)', lower)
                    if match:
                        val = float(match.group(1))
                        unit = match.group(2)
                        gpu_power = val / 1000.0 if unit == "mw" else val
                except Exception:
                    pass

        # If we failed to parse anything but got output, log it to help debugging
        if not all_temps and output.strip():
            logger.info("powermetrics output didn't yield temperatures. Raw output excerpt:\n%s", output[:1000])

        # Update shared state
        if cpu_die is not None:
            self._cpu_die_temp = cpu_die
        if gpu_die is not None:
            self._gpu_die_temp = gpu_die
        if all_temps:
            self._hotspot_temp = max(all_temps)
        if cpu_power is not None:
            self._cpu_power_w = cpu_power
        if gpu_power is not None:
            self._gpu_power_w = gpu_power

    # ------------------------------------------------------------------
    # Fallback temperature methods (no sudo required)
    # ------------------------------------------------------------------

    @safe_execute(None)
    def _fetch_cpu_temp(self) -> Optional[float]:
        """
        Query system temperature sensors.

        On Apple Silicon, psutil cannot read CPU die temperature without root.
        Falls back to battery temperature (divided by 100 to convert from
        Apple's centi-celsius) if available.

        Returns:
            Optional[float]: Temperature in Celsius if sensors exist, else None.
        """
        # Standard psutil path (works on Linux and Intel Macs)
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                sensor_keys = ["coretemp", "cpu_thermal", "k10temp", "acpitz"]
                for key in sensor_keys:
                    if key in temps and temps[key]:
                        return float(temps[key][0].current)
                for sensor_list in temps.values():
                    if sensor_list:
                        return float(sensor_list[0].current)

        # Apple Silicon fallback: read battery sensor temp from ioreg
        if self._is_apple_silicon:
            try:
                result = subprocess.run(
                    ["ioreg", "-rc", "AppleSmartBattery"],
                    capture_output=True, text=True, timeout=3
                )
                for line in result.stdout.splitlines():
                    stripped = line.strip()
                    # Match exact "Temperature" = XXXX (centi-celsius)
                    if stripped.startswith('"Temperature"'):
                        val_str = stripped.split("=")[-1].strip()
                        raw = int(val_str)
                        return round(raw / 100.0, 1)
            except Exception as e:
                logger.debug("Failed to read battery temp: %s", e)

        return None

    @safe_execute("Normal")
    def _fetch_thermal_pressure(self) -> str:
        """
        Query macOS pmset for thermal throttling state.
        Returns a human-readable label like 'Normal', 'Fair', 'Serious', or 'Critical'.

        On non-macOS systems, returns 'N/A'.
        """
        if sys.platform != "darwin":
            return "N/A"

        try:
            result = subprocess.run(
                ["pmset", "-g", "therm"],
                capture_output=True, text=True, timeout=3
            )
            output = result.stdout.lower()
            if "no thermal warning" in output and "no performance warning" in output:
                return "Normal"
            elif "nominal" in output:
                return "Normal"
            elif "fair" in output:
                return "Fair"
            elif "serious" in output:
                return "Serious"
            elif "critical" in output:
                return "Critical"
            else:
                return "Normal"
        except Exception:
            return "N/A"

    def collect(self) -> CPUData:
        """
        Gather real-time CPU performance statistics.

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
        thermal = self._fetch_thermal_pressure()

        return CPUData(
            model=self._model,
            architecture=self._architecture,
            physical_cores=self._physical_cores,
            logical_cores=self._logical_cores,
            performance_cores=self._perf_cores,
            efficiency_cores=self._eff_cores,
            gpu_cores=self._gpu_cores,
            npu_cores=self._npu_cores,
            usage_overall=usage_overall,
            usage_per_core=usage_per_core,
            frequency_current=freq_current,
            frequency_max=freq_max,
            temperature=temp,
            cpu_die_temp=self._cpu_die_temp,
            gpu_die_temp=self._gpu_die_temp,
            hotspot_temp=self._hotspot_temp,
            cpu_power_w=self._cpu_power_w,
            gpu_power_w=self._gpu_power_w,
            thermal_pressure=thermal,
        )
