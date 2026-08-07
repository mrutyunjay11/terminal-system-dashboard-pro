"""
Battery metrics collection module for the Terminal System Dashboard Pro.
Monitors battery state of charge, power source, remaining runtime, and detailed diagnostics.
Designed for Windows and Linux systems.
"""

import os
import sys
import logging
import psutil
from dataclasses import dataclass
from typing import Optional
from utils import safe_execute

logger = logging.getLogger("Battery")


@dataclass
class BatteryData:
    """
    Dataclass representing collected Battery metrics.
    """
    has_battery: bool
    percent: float
    power_plugged: bool
    secsleft: int
    charging: bool
    time_remaining_str: str
    health: Optional[str] = 'N/A'
    temperature: Optional[float] = None
    virtual_temperature: Optional[float] = None
    max_lifetime_temp: Optional[float] = None
    min_lifetime_temp: Optional[float] = None
    cycle_count: Optional[int] = None
    design_capacity: Optional[int] = None
    nominal_capacity: Optional[int] = None
    max_capacity_pct: Optional[int] = None
    wear_level_pct: Optional[float] = None
    is_failed: Optional[bool] = None
    voltage_v: Optional[float] = None
    amperage_ma: Optional[float] = None


class BatteryCollector:
    """
    Retrieves system power levels and charging state via platform hardware abstraction.
    On Linux, queries /sys/class/power_supply for detailed diagnostics.
    On Windows, uses psutil with placeholder for detailed diagnostics.
    """

    def __init__(self) -> None:
        """Initialize the Battery Collector."""
        logger.info("Initializing Battery Collector...")

    def _fetch_linux_battery_details(self) -> dict:
        """
        Read detailed battery metrics from /sys/class/power_supply on Linux.

        Returns:
            dict: Parsed battery properties.
        """
        details = {}
        if sys.platform != "linux":
            return details

        sys_power = "/sys/class/power_supply"
        bat_path = None
        if os.path.exists(os.path.join(sys_power, "BAT0")):
            bat_path = os.path.join(sys_power, "BAT0")
        elif os.path.exists(os.path.join(sys_power, "BAT1")):
            bat_path = os.path.join(sys_power, "BAT1")
        
        if not bat_path:
            return details

        def read_sys_file(filename: str, is_float: bool = False, divide: float = 1.0):
            filepath = os.path.join(bat_path, filename)
            try:
                if os.path.exists(filepath):
                    with open(filepath, 'r') as f:
                        val = f.read().strip()
                        if not val:
                            return None
                        if is_float:
                            return round(float(val) / divide, 2)
                        else:
                            return int(int(val) / divide)
            except Exception as e:
                logger.debug("Failed to read %s: %s", filename, e)
            return None

        def read_sys_str(filename: str) -> Optional[str]:
            filepath = os.path.join(bat_path, filename)
            try:
                if os.path.exists(filepath):
                    with open(filepath, 'r') as f:
                        return f.read().strip()
            except Exception as e:
                logger.debug("Failed to read %s: %s", filename, e)
            return None

        details["cycle_count"] = read_sys_file("cycle_count")

        # Try charge_full_design or energy_full_design
        design = read_sys_file("charge_full_design", divide=1000.0)
        if design is None:
            design = read_sys_file("energy_full_design", divide=1000.0)
        details["design_capacity"] = design

        # Try charge_full or energy_full
        nominal = read_sys_file("charge_full", divide=1000.0)
        if nominal is None:
            nominal = read_sys_file("energy_full", divide=1000.0)
        details["nominal_capacity"] = nominal

        details["voltage_v"] = read_sys_file("voltage_now", is_float=True, divide=1000000.0)

        current = read_sys_file("current_now", divide=1000.0)
        status = read_sys_str("status")

        if current is not None:
            if status == "Discharging":
                details["amperage_ma"] = -float(current)
            else:
                details["amperage_ma"] = float(current)

        details["temperature"] = read_sys_file("temp", is_float=True, divide=10.0)

        if nominal is not None and design is not None and design > 0:
            details["max_capacity_pct"] = int((nominal / design) * 100)
            details["wear_level_pct"] = round((1.0 - (nominal / design)) * 100.0, 1)

        return details

    def _fetch_windows_battery_details(self) -> dict:
        """
        Placeholder for future Windows detailed battery metrics.
        
        Returns:
            dict: Empty dictionary as Windows does not easily expose these via simple APIs.
        """
        return {}

    def collect(self) -> BatteryData:
        """
        Query system battery indicators and status parameters.

        Returns:
            BatteryData: The populated Battery metrics dataclass.
        """
        try:
            battery = psutil.sensors_battery()
        except Exception as e:
            logger.debug("Failed reading battery hardware status: %s", e)
            battery = None

        if battery is None:
            return BatteryData(
                has_battery=False,
                percent=0.0,
                power_plugged=True,
                secsleft=-1,
                charging=False,
                time_remaining_str="N/A (No Battery)",
                health="N/A",
            )

        percent = float(battery.percent)
        power_plugged = bool(battery.power_plugged)
        secsleft = int(battery.secsleft)

        # Determine charging state
        # If plugged in and not at 100%, we are charging or fully charged
        charging = power_plugged and percent < 100.0

        # Build readable remaining runtime label
        if power_plugged:
            if percent >= 99.0:
                time_remaining_str = "Fully Charged"
            else:
                time_remaining_str = "Charging (AC Power)"
        elif secsleft == psutil.POWER_TIME_UNKNOWN:
            time_remaining_str = "Calculating..."
        elif secsleft == psutil.POWER_TIME_UNLIMITED:
            time_remaining_str = "Unlimited (AC Power)"
        else:
            # Convert secsleft to hours and minutes
            hours = secsleft // 3600
            minutes = (secsleft % 3600) // 60
            time_remaining_str = f"{hours}h {minutes}m"

        health = "Good"
        
        if sys.platform == "linux":
            plat_details = self._fetch_linux_battery_details()
        elif sys.platform == "win32":
            plat_details = self._fetch_windows_battery_details()
        else:
            plat_details = {}

        if plat_details.get("is_failed"):
            health = "Failing/Dead"
        elif plat_details.get("max_capacity_pct") is not None:
            cap = plat_details["max_capacity_pct"]
            if cap > 80:
                health = f"Good ({cap}%)"
            elif cap > 50:
                health = f"Service Required ({cap}%)"
            else:
                health = f"Degraded ({cap}%)"

        return BatteryData(
            has_battery=True,
            percent=percent,
            power_plugged=power_plugged,
            secsleft=secsleft,
            charging=charging,
            time_remaining_str=time_remaining_str,
            health=health,
            temperature=plat_details.get("temperature"),
            virtual_temperature=plat_details.get("virtual_temperature"),
            max_lifetime_temp=plat_details.get("max_lifetime_temp"),
            min_lifetime_temp=plat_details.get("min_lifetime_temp"),
            cycle_count=plat_details.get("cycle_count"),
            design_capacity=plat_details.get("design_capacity"),
            nominal_capacity=plat_details.get("nominal_capacity"),
            max_capacity_pct=plat_details.get("max_capacity_pct"),
            wear_level_pct=plat_details.get("wear_level_pct"),
            is_failed=plat_details.get("is_failed"),
            voltage_v=plat_details.get("voltage_v"),
            amperage_ma=plat_details.get("amperage_ma"),
        )
