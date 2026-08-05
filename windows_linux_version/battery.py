"""
Battery metrics collection module for the Terminal System Dashboard Pro.
Monitors battery state of charge, power source, remaining runtime, and detailed diagnostics.
"""

import os
import sys
import re
import logging
import subprocess
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
    health: Optional[str] = "N/A"
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
    On macOS/Darwin, queries AppleSmartBattery via ioreg for detailed diagnostics.
    """

    def __init__(self) -> None:
        """Initialize the Battery Collector."""
        logger.info("Initializing Battery Collector...")

    def _fetch_macos_battery_details(self) -> dict:
        """
        Run ioreg and parse detailed battery metrics on macOS.

        Returns:
            dict: Parsed battery properties.
        """
        details = {}
        if sys.platform != "darwin":
            return details

        try:
            result = subprocess.run(
                ["ioreg", "-rc", "AppleSmartBattery"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode != 0:
                return details

            text = result.stdout

            def search_val(pattern, is_float=False, divide=1.0):
                m = re.search(pattern, text)
                if m:
                    val = float(m.group(1)) if is_float else int(m.group(1))
                    return round(val / divide, 2) if is_float else val
                return None

            details["temperature"] = search_val(r'\"Temperature\" = (\d+)', is_float=True, divide=100.0)
            details["virtual_temperature"] = search_val(r'\"VirtualTemperature\" = (\d+)', is_float=True, divide=100.0)
            details["cycle_count"] = search_val(r'\"CycleCount\" = (\d+)')
            details["design_capacity"] = search_val(r'\"DesignCapacity\" = (\d+)')
            details["nominal_capacity"] = search_val(r'\"NominalChargeCapacity\" = (\d+)')
            details["max_capacity_pct"] = search_val(r'\"MaxCapacity\" = (\d+)')
            
            failed = search_val(r'\"PermanentFailureStatus\" = (\d+)')
            if failed is not None:
                details["is_failed"] = failed != 0

            details["voltage_v"] = search_val(r'\"Voltage\" = (\d+)', is_float=True, divide=1000.0)

            amp = search_val(r'\"Amperage\" = (\d+)')
            if amp is not None:
                if amp > 2**63:
                    amp -= 2**64
                details["amperage_ma"] = float(amp)

            details["max_lifetime_temp"] = search_val(r'\"MaximumTemperature\"=(\d+)', is_float=True)
            details["min_lifetime_temp"] = search_val(r'\"MinimumTemperature\"=(\d+)', is_float=True)

            if details.get("nominal_capacity") and details.get("design_capacity"):
                nom = details["nominal_capacity"]
                des = details["design_capacity"]
                if des > 0:
                    details["wear_level_pct"] = round((1.0 - (nom / des)) * 100.0, 1)

        except Exception as e:
            logger.debug("Failed parsing macOS ioreg battery details: %s", e)

        return details

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
        macos_details = self._fetch_macos_battery_details()
        if macos_details.get("is_failed"):
            health = "Failing/Dead"
        elif macos_details.get("max_capacity_pct") is not None:
            cap = macos_details["max_capacity_pct"]
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
            temperature=macos_details.get("temperature"),
            virtual_temperature=macos_details.get("virtual_temperature"),
            max_lifetime_temp=macos_details.get("max_lifetime_temp"),
            min_lifetime_temp=macos_details.get("min_lifetime_temp"),
            cycle_count=macos_details.get("cycle_count"),
            design_capacity=macos_details.get("design_capacity"),
            nominal_capacity=macos_details.get("nominal_capacity"),
            max_capacity_pct=macos_details.get("max_capacity_pct"),
            wear_level_pct=macos_details.get("wear_level_pct"),
            is_failed=macos_details.get("is_failed"),
            voltage_v=macos_details.get("voltage_v"),
            amperage_ma=macos_details.get("amperage_ma"),
        )
