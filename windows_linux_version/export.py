"""
Report export module for the Terminal System Dashboard Pro (Windows & Linux).
Supports exporting SystemState models to JSON, CSV, and formatted text documents.
"""

import os
import csv
import json
import logging
from datetime import datetime
from dataclasses import asdict
from typing import Dict, Any

from monitor import SystemState
from utils import format_bytes

logger = logging.getLogger("Export")


class Exporter:
    """
    Serializes and writes system status snap-shots to persistent files on disk.
    Creates and manages an 'exports/' output subdirectory.
    """

    def __init__(self, export_dir: str = "exports") -> None:
        """
        Initialize the Exporter and establish the output path.

        Args:
            export_dir (str): Relative folder name for stored reports.
        """
        # Ensure the exports folder exists relative to the file location
        project_root = os.path.dirname(os.path.abspath(__file__))
        self.export_dir = os.path.join(project_root, export_dir)
        os.makedirs(self.export_dir, exist_ok=True)

    def generate_filename(self, format_type: str) -> str:
        """
        Create a unique, timestamped destination path.

        Args:
            format_type (str): File extension (json, csv, txt).

        Returns:
            str: Absolute path destination.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.export_dir, f"system_report_{timestamp}.{format_type}")

    def export(self, state: SystemState, format_type: str) -> str:
        """
        Export a snapshot of the current SystemState in the requested format.

        Args:
            state (SystemState): The system status metrics snapshot.
            format_type (str): Output format type ('json', 'csv', 'txt').

        Returns:
            str: The absolute path to the generated file.

        Raises:
            ValueError: If the format_type is unsupported.
        """
        normalized_format = format_type.strip().lower()
        filepath = self.generate_filename(normalized_format)

        if normalized_format == "json":
            self._to_json(state, filepath)
        elif normalized_format == "csv":
            self._to_csv(state, filepath)
        elif normalized_format == "txt":
            self._to_txt(state, filepath)
        else:
            logger.error("Unsupported export format requested: %s", format_type)
            raise ValueError(f"Unsupported export format: {format_type}. Use json, csv, or txt.")

        logger.info("Exported system metrics successfully (Format: %s) -> %s", normalized_format, filepath)
        return filepath

    def _to_json(self, state: SystemState, filepath: str) -> None:
        """Serialize SystemState to standard indented JSON format."""
        data = asdict(state)
        # Supplement raw dictionary with a human-readable ISO formatted datetime
        data["formatted_time"] = datetime.fromtimestamp(state.timestamp).isoformat()
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _to_csv(self, state: SystemState, filepath: str) -> None:
        """Flatten SystemState metrics into columns and export as key-value rows in a CSV."""
        flat_data = self._flatten_state(state)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric Label", "Value"])
            for key, val in flat_data.items():
                writer.writerow([key, str(val)])

    def _to_txt(self, state: SystemState, filepath: str) -> None:
        """Generate a clean ASCII formatted text layout report."""
        lines = [
            "=" * 60,
            "TERMINAL SYSTEM DASHBOARD PRO REPORT",
            f"Generated at: {datetime.fromtimestamp(state.timestamp).strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            "",
            "[SYSTEM INFORMATION]",
            f"  OS System      : {state.os.system} {state.os.release}",
            f"  Kernel Version : {state.os.version}",
            f"  Architecture   : {state.os.machine}",
            f"  Processor Name : {state.os.processor}",
            f"  System Uptime  : {state.os.uptime_str}",
            f"  Logged-in User : {state.os.username}",
            f"  Python Runtime : {state.os.python_version}",
            "",
            "[CPU SPECIFICATIONS & LOAD]",
            f"  Model          : {state.cpu.model}",
            f"  Architecture   : {state.cpu.architecture}",
            f"  Physical Cores : {state.cpu.physical_cores}",
            f"  Logical Cores  : {state.cpu.logical_cores}",
            f"  Overall Load   : {state.cpu.usage_overall:.1f}%",
            f"  Current Freq   : {state.cpu.frequency_current:.1f} MHz (Max: {state.cpu.frequency_max:.1f} MHz)",
        ]

        temp_str = f"{state.cpu.temperature:.1f} °C" if state.cpu.temperature else "N/A"
        lines.append(f"  CPU Temp       : {temp_str}")
        
        cpu_power_str = f"{state.cpu.cpu_power_w:.2f} W" if state.cpu.cpu_power_w is not None else "N/A"
        lines.append(f"  CPU Power Draw : {cpu_power_str}")
        lines.append(f"  Thermal State  : {state.cpu.thermal_pressure}")

        # GPU Info
        if state.cpu.gpu_name is not None:
            lines.append("")
            lines.append("[GPU INFORMATION (NVIDIA)]")
            lines.append(f"  GPU Name       : {state.cpu.gpu_name}")
            gpu_temp_str = f"{state.cpu.gpu_temp:.1f} °C" if state.cpu.gpu_temp is not None else "N/A"
            lines.append(f"  GPU Temp       : {gpu_temp_str}")
            gpu_load_str = f"{state.cpu.gpu_load:.1f}%" if state.cpu.gpu_load is not None else "N/A"
            lines.append(f"  GPU Load       : {gpu_load_str}")
            if state.cpu.gpu_memory_used is not None and state.cpu.gpu_memory_total is not None:
                lines.append(f"  GPU VRAM Used  : {state.cpu.gpu_memory_used:.0f} / {state.cpu.gpu_memory_total:.0f} MB")
            gpu_power_str = f"{state.cpu.gpu_power_w:.1f} W" if state.cpu.gpu_power_w is not None else "N/A"
            lines.append(f"  GPU Power Draw : {gpu_power_str}")

        lines.append("")

        lines.extend([
            "[MEMORY UTILIZATION]",
            f"  RAM Total      : {format_bytes(state.memory.ram_total)}",
            f"  RAM Used       : {format_bytes(state.memory.ram_used)} ({state.memory.ram_percent:.1f}%)",
            f"  RAM Available  : {format_bytes(state.memory.ram_available)}",
            f"  Swap Total     : {format_bytes(state.memory.swap_total)}",
            f"  Swap Used      : {format_bytes(state.memory.swap_used)} ({state.memory.swap_percent:.1f}%)",
            "",
            "[DISK STORAGE]",
        ])

        for i, part in enumerate(state.disk.partitions):
            lines.extend([
                f"  Partition {i+1}:",
                f"    Device       : {part.device}",
                f"    Mountpoint   : {part.mountpoint}",
                f"    Filesystem   : {part.fstype}",
                f"    Total Size   : {format_bytes(part.total)}",
                f"    Used Size    : {format_bytes(part.used)} ({part.percent:.1f}%)",
                f"    Free Size    : {format_bytes(part.free)}",
            ])

        lines.extend([
            f"  Disk Read Speed: {format_bytes(int(state.disk.read_speed))}/s",
            f"  Disk Write Spd : {format_bytes(int(state.disk.write_speed))}/s",
            "",
            "[NETWORK CONFIGURATION & SPEED]",
            f"  Hostname       : {state.network.hostname}",
            f"  Local IP       : {state.network.local_ip}",
            f"  Internet Status: {'Online' if state.network.online else 'Offline'}",
            f"  Upload Speed   : {format_bytes(int(state.network.upload_speed))}/s",
            f"  Download Speed : {format_bytes(int(state.network.download_speed))}/s",
            f"  Total Uploaded : {format_bytes(state.network.total_sent)}",
            f"  Total Received : {format_bytes(state.network.total_recv)}",
        ])

        if state.network.speedtest_download is not None:
            lines.extend([
                f"  Speedtest Down : {state.network.speedtest_download:.2f} Mbps",
                f"  Speedtest Up   : {state.network.speedtest_upload:.2f} Mbps",
            ])

        lines.extend([
            "",
            "[BATTERY STATE]",
        ])

        if state.battery.has_battery:
            lines.extend([
                f"  Percentage     : {state.battery.percent:.1f}%",
                f"  Power Source   : {'AC Power' if state.battery.power_plugged else 'Battery Power'}",
                f"  Time Remaining : {state.battery.time_remaining_str}",
                f"  Battery Health : {state.battery.health}",
            ])
            if state.battery.temperature is not None:
                lines.append(f"  Temperature    : {state.battery.temperature:.1f} °C")
            if state.battery.cycle_count is not None:
                lines.append(f"  Cycle Count    : {state.battery.cycle_count}")
            if state.battery.wear_level_pct is not None:
                lines.append(f"  Wear Level     : {state.battery.wear_level_pct:.1f}%")
            if state.battery.voltage_v is not None:
                lines.append(f"  Voltage        : {state.battery.voltage_v:.2f} V")
            if state.battery.amperage_ma is not None:
                lines.append(f"  Amperage       : {state.battery.amperage_ma:.0f} mA")
            if state.battery.design_capacity is not None:
                lines.append(f"  Design Cap     : {state.battery.design_capacity} mAh")
            if state.battery.nominal_capacity is not None:
                lines.append(f"  Current Cap    : {state.battery.nominal_capacity} mAh")
        else:
            lines.append("  No Battery Detected")

        lines.extend([
            "",
            "[TOP 10 CPU CONSUMING PROCESSES]",
        ])
        for proc in state.top_cpu_processes:
            lines.append(f"  PID: {proc.pid:<6} | CPU: {proc.cpu_percent:>5.1f}% | Name: {proc.name}")

        lines.extend([
            "",
            "[TOP 10 MEMORY CONSUMING PROCESSES]",
        ])
        for proc in state.top_mem_processes:
            lines.append(f"  PID: {proc.pid:<6} | RAM: {format_bytes(proc.memory_rss):>10} | Name: {proc.name}")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _flatten_state(self, state: SystemState) -> Dict[str, Any]:
        """
        Flattens nested SystemState metrics into a single-level dictionary.

        Args:
            state (SystemState): The system status metrics snapshot.

        Returns:
            Dict[str, Any]: Key-value pairs of system metrics.
        """
        res: Dict[str, Any] = {
            "OS_System": state.os.system,
            "OS_Release": state.os.release,
            "OS_Version": state.os.version,
            "OS_Machine": state.os.machine,
            "OS_Processor": state.os.processor,
            "OS_Uptime": state.os.uptime_str,
            "OS_Username": state.os.username,
            "OS_PythonVersion": state.os.python_version,
            
            "CPU_Model": state.cpu.model,
            "CPU_Architecture": state.cpu.architecture,
            "CPU_PhysicalCores": state.cpu.physical_cores,
            "CPU_LogicalCores": state.cpu.logical_cores,
            "CPU_UsageOverall_Pct": state.cpu.usage_overall,
            "CPU_FreqCurrent_MHz": state.cpu.frequency_current,
            "CPU_FreqMax_MHz": state.cpu.frequency_max,
            "CPU_Temperature_C": state.cpu.temperature if state.cpu.temperature is not None else "N/A",
            "CPU_Power_W": state.cpu.cpu_power_w if state.cpu.cpu_power_w is not None else "N/A",
            "CPU_ThermalPressure": state.cpu.thermal_pressure,

            # GPU (NVIDIA)
            "GPU_Name": state.cpu.gpu_name if state.cpu.gpu_name is not None else "N/A",
            "GPU_Temperature_C": state.cpu.gpu_temp if state.cpu.gpu_temp is not None else "N/A",
            "GPU_Load_Pct": state.cpu.gpu_load if state.cpu.gpu_load is not None else "N/A",
            "GPU_MemoryUsed_MB": state.cpu.gpu_memory_used if state.cpu.gpu_memory_used is not None else "N/A",
            "GPU_MemoryTotal_MB": state.cpu.gpu_memory_total if state.cpu.gpu_memory_total is not None else "N/A",
            "GPU_Power_W": state.cpu.gpu_power_w if state.cpu.gpu_power_w is not None else "N/A",
            
            "RAM_Total_Bytes": state.memory.ram_total,
            "RAM_Used_Bytes": state.memory.ram_used,
            "RAM_Available_Bytes": state.memory.ram_available,
            "RAM_Used_Pct": state.memory.ram_percent,
            "Swap_Total_Bytes": state.memory.swap_total,
            "Swap_Used_Bytes": state.memory.swap_used,
            "Swap_Used_Pct": state.memory.swap_percent,
            
            "Disk_ReadSpeed_Bps": state.disk.read_speed,
            "Disk_WriteSpeed_Bps": state.disk.write_speed,
            
            "Net_Hostname": state.network.hostname,
            "Net_LocalIP": state.network.local_ip,
            "Net_Online": state.network.online,
            "Net_UploadSpeed_Bps": state.network.upload_speed,
            "Net_DownloadSpeed_Bps": state.network.download_speed,
            "Net_TotalSent_Bytes": state.network.total_sent,
            "Net_TotalRecv_Bytes": state.network.total_recv,
            
            "Battery_HasBattery": state.battery.has_battery,
        }

        # Add disk partitions
        for i, part in enumerate(state.disk.partitions):
            res[f"Disk_Part{i+1}_Device"] = part.device
            res[f"Disk_Part{i+1}_Mountpoint"] = part.mountpoint
            res[f"Disk_Part{i+1}_Fstype"] = part.fstype
            res[f"Disk_Part{i+1}_Total"] = part.total
            res[f"Disk_Part{i+1}_Used"] = part.used
            res[f"Disk_Part{i+1}_Used_Pct"] = part.percent

        if state.network.speedtest_download is not None:
            res["Net_SpeedtestDownload_Mbps"] = state.network.speedtest_download
            res["Net_SpeedtestUpload_Mbps"] = state.network.speedtest_upload

        if state.battery.has_battery:
            res["Battery_Percent"] = state.battery.percent
            res["Battery_Plugged"] = state.battery.power_plugged
            res["Battery_TimeRemaining"] = state.battery.time_remaining_str
            res["Battery_Health"] = state.battery.health
            res["Battery_Temperature_C"] = state.battery.temperature if state.battery.temperature is not None else "N/A"
            res["Battery_CycleCount"] = state.battery.cycle_count if state.battery.cycle_count is not None else "N/A"
            res["Battery_DesignCapacity_mAh"] = state.battery.design_capacity if state.battery.design_capacity is not None else "N/A"
            res["Battery_NominalCapacity_mAh"] = state.battery.nominal_capacity if state.battery.nominal_capacity is not None else "N/A"
            res["Battery_WearLevel_Pct"] = state.battery.wear_level_pct if state.battery.wear_level_pct is not None else "N/A"
            res["Battery_Voltage_V"] = state.battery.voltage_v if state.battery.voltage_v is not None else "N/A"
            res["Battery_Amperage_mA"] = state.battery.amperage_ma if state.battery.amperage_ma is not None else "N/A"

        return res
