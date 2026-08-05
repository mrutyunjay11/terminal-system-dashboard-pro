"""
Dashboard user interface rendering module for the Terminal System Dashboard Pro.
Builds the Rich layout, manages the live render loop, and handles non-blocking keyboard shortcuts.
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Optional, List, Dict

from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.progress import ProgressBar
from rich.text import Text
from rich.align import Align
from rich import box
from rich.columns import Columns

from config import AppConfig, save_config
from themes import get_theme, ThemeColors, THEMES
from monitor import SystemMonitor, SystemState
from export import Exporter
from utils import format_bytes

logger = logging.getLogger("Dashboard")

# Non-blocking terminal input configuration
if sys.platform != "win32":
    import select
    import termios
    import tty

    class NonBlockingInput:
        """Context manager to enable non-blocking keyboard reading under Unix-like OS."""
        def __enter__(self) -> "NonBlockingInput":
            self.fd = sys.stdin.fileno()
            try:
                self.old_settings = termios.tcgetattr(self.fd)
                tty.setcbreak(self.fd)
            except termios.error:
                self.old_settings = None
            return self

        def __exit__(self, exc_type: Exception, exc_val: Exception, exc_tb: Exception) -> None:
            if self.old_settings is not None:
                termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

        def get_char(self) -> Optional[str]:
            """Retrieve the pressed key buffer if any, non-blockingly."""
            if self.old_settings is not None and select.select([sys.stdin], [], [], 0.0)[0]:
                return sys.stdin.read(1)
            return None
else:
    import msvcrt

    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    class NonBlockingInput:
        """Context manager to enable non-blocking keyboard reading under Windows OS."""
        def __enter__(self) -> "NonBlockingInput":
            return self

        def __exit__(self, exc_type: Exception, exc_val: Exception, exc_tb: Exception) -> None:
            pass

        def get_char(self) -> Optional[str]:
            """Check keyboard buffer and pull key if hit."""
            if msvcrt.kbhit():
                try:
                    ch = msvcrt.getch()
                    # Handle special key prefixes on Windows (0x00 or 0xE0)
                    if ch in (b"\x00", b"\xe0"):
                        if msvcrt.kbhit():
                            msvcrt.getch()  # consume second byte of special key
                        return None
                    return ch.decode("utf-8", errors="ignore")
                except (UnicodeDecodeError, AttributeError):
                    return None
            return None


class Dashboard:
    """
    Assembles the Rich Layout compartments and handles real-time keyboard inputs.
    """

    def __init__(self, config: AppConfig) -> None:
        """
        Initialize components of the dashboard TUI.

        Args:
            config (AppConfig): Initial startup settings.
        """
        logger.info("Initializing TUI Dashboard...")
        self.config = config
        self.monitor = SystemMonitor()
        self.exporter = Exporter()
        self.console = Console()
        self.theme: ThemeColors = get_theme(config.theme)
        
        # State variables
        self.export_message: str = ""
        self.export_msg_time: float = 0.0

    def cycle_theme(self) -> None:
        """Advance current active theme to the next available style."""
        available_keys = list(THEMES.keys())
        current_idx = available_keys.index(self.config.theme)
        next_idx = (current_idx + 1) % len(available_keys)
        next_theme = available_keys[next_idx]

        self.config.theme = next_theme
        self.theme = get_theme(next_theme)
        save_config(self.config)
        logger.info("Theme switched dynamically to: %s", next_theme)

    def trigger_export(self, state: SystemState) -> None:
        """Write current telemetry state to disk."""
        try:
            filepath = self.exporter.export(state, self.config.export_format)
            filename = os.path.basename(filepath)
            self.export_message = f"Exported: {filename}"
            self.export_msg_time = time.time()
        except Exception as e:
            self.export_message = f"Export Failed: {str(e)[:20]}"
            self.export_msg_time = time.time()
            logger.error("Failed running dynamically triggered export: %s", e)

    def create_layout(self) -> Layout:
        """
        Define screen split containers for the Rich Layout structure.

        Returns:
            Layout: Structured screen layout frame.
        """
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )

        layout["body"].split_row(
            Layout(name="left", ratio=12),
            Layout(name="right", ratio=13),
        )

        layout["left"].split_column(
            Layout(name="cpu_info", ratio=11),
            Layout(name="memory_disk", ratio=9),
            Layout(name="battery", size=8),
        )

        layout["right"].split_column(
            Layout(name="network", ratio=9),
            Layout(name="processes", ratio=11),
        )

        return layout

    def populate_layout(self, layout: Layout, state: SystemState) -> None:
        """
        Inject dynamic content renderables into targeted layout nodes.

        Args:
            layout (Layout): The layout node frame.
            state (SystemState): The system status metrics snapshot.
        """
        t = self.theme

        # ------------------ HEADER ------------------
        title = Text(" TERMINAL SYSTEM DASHBOARD PRO ", style=f"bold {t.title} on {t.border}")
        details = (
            f" [bold {t.accent}]OS:[/] {state.os.system} {state.os.release} | "
            f"[bold {t.accent}]Uptime:[/] {state.os.uptime_str} | "
            f"[bold {t.accent}]User:[/] {state.os.username} | "
            f"[bold {t.accent}]Python:[/] {state.os.python_version}"
        )
        layout["header"].update(
            Panel(
                Align.center(Text.from_markup(details), vertical="middle"),
                title=title,
                border_style=t.border,
                box=box.ROUNDED if hasattr(sys.modules.get("rich.box"), "ROUNDED") else None,
            )
        )

        # ------------------ CPU ------------------
        cpu_table = Table.grid(expand=True)
        cpu_table.add_column(ratio=1)

        # Line 1: Model
        cpu_table.add_row(
            Text.from_markup(f"[bold {t.accent}]Model :[/] {state.cpu.model}")
        )

        # Line 2: Architecture + Core breakdown
        if state.cpu.performance_cores is not None and state.cpu.efficiency_cores is not None:
            cores_str = (
                f"{state.cpu.physical_cores} Total "
                f"({state.cpu.performance_cores}P + {state.cpu.efficiency_cores}E)"
            )
        else:
            cores_str = f"{state.cpu.physical_cores}P / {state.cpu.logical_cores}L"
        cpu_table.add_row(
            Text.from_markup(
                f"[bold {t.accent}]Arch  :[/] {state.cpu.architecture} | "
                f"[bold {t.accent}]CPU Cores:[/] {cores_str}"
            )
        )

        # Line 3: GPU and NPU cores (if available)
        extras = []
        if state.cpu.gpu_cores is not None:
            extras.append(f"[bold {t.accent}]GPU Cores:[/] {state.cpu.gpu_cores}")
        if state.cpu.npu_cores is not None:
            extras.append(f"[bold {t.accent}]Neural Engine:[/] {state.cpu.npu_cores}-core")
        if extras:
            cpu_table.add_row(Text.from_markup(" | ".join(extras)))

        # Line 4: Frequency + Thermal Pressure
        # Color-code thermal pressure
        tp = state.cpu.thermal_pressure
        if tp == "Normal":
            tp_color = t.success
        elif tp == "Fair":
            tp_color = t.warning
        else:
            tp_color = t.danger

        # Line 4: Frequency + Power Draw
        power_str = ""
        if state.cpu.cpu_power_w is not None:
            power_str += f" | [bold {t.accent}]CPU Power:[/] {state.cpu.cpu_power_w:.2f} W"
        if state.cpu.gpu_power_w is not None:
            power_str += f" | [bold {t.accent}]GPU Power:[/] {state.cpu.gpu_power_w:.2f} W"

        cpu_table.add_row(
            Text.from_markup(
                f"[bold {t.accent}]Freq  :[/] {state.cpu.frequency_current:.0f} / "
                f"{state.cpu.frequency_max:.0f} MHz | "
                f"[bold {t.accent}]Thermal:[/] [{tp_color}]{tp}[/]"
                f"{power_str}"
            )
        )

        # Line 5: Temperature readings row
        def _temp_color(val: Optional[float]) -> str:
            """Return a Rich color string based on temperature severity."""
            if val is None:
                return t.text
            if val > 90.0:
                return t.danger
            elif val > 70.0:
                return t.warning
            return t.success

        temp_parts = []
        # CPU Die (from powermetrics, requires sudo)
        if state.cpu.cpu_die_temp is not None:
            c = _temp_color(state.cpu.cpu_die_temp)
            temp_parts.append(f"[bold {t.accent}]CPU Die:[/] [{c}]{state.cpu.cpu_die_temp:.1f}°C[/]")

        # GPU Die (from powermetrics, requires sudo)
        if state.cpu.gpu_die_temp is not None:
            c = _temp_color(state.cpu.gpu_die_temp)
            temp_parts.append(f"[bold {t.accent}]GPU Die:[/] [{c}]{state.cpu.gpu_die_temp:.1f}°C[/]")

        # Hotspot (max of all powermetrics sensors)
        if state.cpu.hotspot_temp is not None:
            c = _temp_color(state.cpu.hotspot_temp)
            temp_parts.append(f"[bold {t.accent}]Hotspot:[/] [{c}]{state.cpu.hotspot_temp:.1f}°C[/]")

        # Battery/fallback temp (always available, no sudo)
        if state.cpu.temperature is not None:
            c = _temp_color(state.cpu.temperature)
            # Label differs based on whether die temps are available
            if state.cpu.cpu_die_temp is not None:
                temp_parts.append(f"[bold {t.accent}]Board:[/] [{c}]{state.cpu.temperature:.1f}°C[/]")
            else:
                temp_parts.append(f"[bold {t.accent}]Temp:[/] [{c}]{state.cpu.temperature:.1f}°C[/]")

        if temp_parts:
            cpu_table.add_row(Text.from_markup(" | ".join(temp_parts)))
        else:
            cpu_table.add_row(Text.from_markup(f"[bold {t.accent}]Temp:[/] N/A"))

        # CPU overall usage bar
        bar_color = t.danger if state.cpu.usage_overall > 85.0 else (t.warning if state.cpu.usage_overall > 60.0 else t.success)
        overall_bar = ProgressBar(
            total=100.0,
            completed=state.cpu.usage_overall,
            width=22,
            complete_style=bar_color,
            finished_style=bar_color,
        )

        overall_row = Table.grid(expand=True)
        overall_row.add_column(ratio=3)
        overall_row.add_column(ratio=2)
        overall_row.add_row(
            Text.from_markup(f"[bold {t.accent}]Load  :[/] [bold {bar_color}]{state.cpu.usage_overall:.1f}%[/]"),
            Align.right(overall_bar)
        )
        cpu_table.add_row(Text(""))  # Spacer
        cpu_table.add_row(overall_row)

        # Per-core display with P/E labels
        core_cols = Table.grid(expand=True)
        core_cols.add_column(ratio=1)
        core_cols.add_column(ratio=1)

        p_cores = state.cpu.performance_cores
        e_cores = state.cpu.efficiency_cores
        core_rows_l = []
        core_rows_r = []

        for idx, pct in enumerate(state.cpu.usage_per_core):
            core_bar_color = t.danger if pct > 85.0 else (t.warning if pct > 60.0 else t.success)
            core_bar = ProgressBar(
                total=100.0,
                completed=pct,
                width=8,
                complete_style=core_bar_color,
                finished_style=core_bar_color,
            )

            # Label cores as P0-P3, E0-E3 on Apple Silicon
            if p_cores is not None and e_cores is not None:
                if idx < p_cores:
                    label = f"P{idx}"
                else:
                    label = f"E{idx - p_cores}"
            else:
                label = f"C{idx}"

            core_text = f"{label:<3}{pct:>4.0f}% "
            line = Columns([Text(core_text, style=t.text), core_bar])

            if idx % 2 == 0:
                core_rows_l.append(line)
            else:
                core_rows_r.append(line)

        # Cap length to fit box safely
        max_rows = 4
        core_rows_l = core_rows_l[:max_rows]
        core_rows_r = core_rows_r[:max_rows]

        for left_line, right_line in zip(core_rows_l, core_rows_r):
            core_cols.add_row(left_line, right_line)

        # Handle odd core count — if one column has an extra row
        if len(core_rows_l) > len(core_rows_r):
            core_cols.add_row(core_rows_l[-1], Text(""))

        cpu_layout = Table.grid(expand=True)
        cpu_layout.add_row(cpu_table)
        cpu_layout.add_row(Text(""))  # Spacer
        cpu_layout.add_row(core_cols)

        layout["cpu_info"].update(
            Panel(
                cpu_layout,
                title=f"[bold {t.title}]CPU Info[/]",
                border_style=t.border,
            )
        )

        # ------------------ MEMORY & DISK ------------------
        mem_disk_table = Table.grid(expand=True)
        mem_disk_table.add_column(ratio=1)

        # Memory calculations
        ram_bar_color = t.danger if state.memory.ram_percent > 85.0 else (t.warning if state.memory.ram_percent > 60.0 else t.success)
        ram_bar = ProgressBar(
            total=100.0,
            completed=state.memory.ram_percent,
            width=20,
            complete_style=ram_bar_color,
            finished_style=ram_bar_color,
        )
        mem_disk_table.add_row(
            Columns([
                Text.from_markup(
                    f"[bold {t.accent}]RAM :[/] {format_bytes(state.memory.ram_used)} / "
                    f"{format_bytes(state.memory.ram_total)} ({state.memory.ram_percent:.0f}%)"
                ),
                Align.right(ram_bar)
            ])
        )

        # Swap calculations
        swap_bar_color = t.danger if state.memory.swap_percent > 85.0 else (t.warning if state.memory.swap_percent > 60.0 else t.success)
        swap_bar = ProgressBar(
            total=100.0,
            completed=state.memory.swap_percent,
            width=20,
            complete_style=swap_bar_color,
            finished_style=swap_bar_color,
        )
        mem_disk_table.add_row(
            Columns([
                Text.from_markup(
                    f"[bold {t.accent}]Swap:[/] {format_bytes(state.memory.swap_used)} / "
                    f"{format_bytes(state.memory.swap_total)} ({state.memory.swap_percent:.0f}%)"
                ),
                Align.right(swap_bar)
            ])
        )

        mem_disk_table.add_row(Text(""))  # Spacer

        # Disk Storage Details
        disk_table = Table(
            box=None,
            header_style=f"bold {t.accent}",
            expand=True,
            padding=(0, 1),
        )
        disk_table.add_column("Mount", ratio=2)
        disk_table.add_column("Type", ratio=1)
        disk_table.add_column("Usage", ratio=3)
        disk_table.add_column("Bar", ratio=4)

        # Only list main partitions (up to 4) to prevent layout overflow
        for part in state.disk.partitions[:4]:
            p_color = t.danger if part.percent > 85.0 else (t.warning if part.percent > 60.0 else t.success)
            p_bar = ProgressBar(
                total=100.0,
                completed=part.percent,
                width=10,
                complete_style=p_color,
                finished_style=p_color,
            )
            disk_table.add_row(
                part.mountpoint,
                part.fstype,
                f"{format_bytes(part.used)}/{format_bytes(part.total)}",
                p_bar,
            )

        mem_disk_table.add_row(disk_table)

        # Disk speeds
        speeds_str = (
            f"[bold {t.accent}]Disk Speed - Read:[/] {format_bytes(int(state.disk.read_speed))}/s | "
            f"[bold {t.accent}]Write:[/] {format_bytes(int(state.disk.write_speed))}/s"
        )
        mem_disk_table.add_row(Text(""))  # Spacer
        mem_disk_table.add_row(Text.from_markup(speeds_str))

        layout["memory_disk"].update(
            Panel(
                mem_disk_table,
                title=f"[bold {t.title}]Memory & Storage[/]",
                border_style=t.border,
            )
        )

        # ------------------ BATTERY ------------------
        bat_details = Table.grid(expand=True)
        bat_details.add_column(ratio=1)

        if state.battery.has_battery:
            bat_color = t.danger if state.battery.percent < 20.0 else (t.warning if state.battery.percent < 45.0 else t.success)
            bat_bar = ProgressBar(
                total=100.0,
                completed=state.battery.percent,
                width=15,
                complete_style=bat_color,
                finished_style=bat_color,
            )
            
            charging_icon = " ⚡" if state.battery.charging else ""
            status_row = Table.grid(expand=True)
            status_row.add_column(ratio=3)
            status_row.add_column(ratio=2)
            status_row.add_row(
                Text.from_markup(
                    f"[bold {t.accent}]Power :[/] {state.battery.percent:.0f}%{charging_icon} ({state.battery.time_remaining_str})"
                ),
                Align.right(bat_bar)
            )
            bat_details.add_row(status_row)

            # Temp details
            temp_parts = []
            if state.battery.temperature is not None:
                temp_parts.append(f"[bold {t.accent}]Temp:[/] {state.battery.temperature:.1f}°C")
            if state.battery.virtual_temperature is not None:
                temp_parts.append(f"[bold {t.accent}]Virtual:[/] {state.battery.virtual_temperature:.1f}°C")
            
            # Hotspot / Lifetime Max-Min
            lifetime_parts = []
            if state.battery.max_lifetime_temp is not None:
                lifetime_parts.append(f"Max {state.battery.max_lifetime_temp:.0f}°C")
            if state.battery.min_lifetime_temp is not None:
                lifetime_parts.append(f"Min {state.battery.min_lifetime_temp:.0f}°C")
            if lifetime_parts:
                temp_parts.append(f"[bold {t.accent}]Limits:[/] " + "/".join(lifetime_parts))

            if temp_parts:
                bat_details.add_row(Text.from_markup(" | ".join(temp_parts)))

            # Health details
            health_parts = [f"[bold {t.accent}]Health:[/] {state.battery.health}"]
            if state.battery.cycle_count is not None:
                health_parts.append(f"[bold {t.accent}]Cycles:[/] {state.battery.cycle_count}")
            if state.battery.wear_level_pct is not None:
                health_parts.append(f"[bold {t.accent}]Wear:[/] {state.battery.wear_level_pct:.1f}%")
            bat_details.add_row(Text.from_markup(" | ".join(health_parts)))

            # Electrical details (Voltage, Amperage)
            elec_parts = []
            if state.battery.voltage_v is not None:
                elec_parts.append(f"[bold {t.accent}]Voltage:[/] {state.battery.voltage_v:.2f} V")
            if state.battery.amperage_ma is not None:
                prefix = "+" if state.battery.amperage_ma > 0 else ""
                elec_parts.append(f"[bold {t.accent}]Current:[/] {prefix}{state.battery.amperage_ma:.0f} mA")
            if state.battery.design_capacity is not None:
                elec_parts.append(f"[bold {t.accent}]Design Cap:[/] {state.battery.design_capacity} mAh")

            if elec_parts:
                bat_details.add_row(Text.from_markup(" | ".join(elec_parts)))

        else:
            bat_details.add_row(
                Text.from_markup(f"[bold {t.accent}]Power source:[/] AC (No Battery Detected)"),
            )

        layout["battery"].update(
            Panel(
                bat_details,
                title=f"[bold {t.title}]Power & Battery[/]",
                border_style=t.border,
            )
        )

        # ------------------ NETWORK ------------------
        net_table = Table.grid(expand=True)
        net_table.add_column(ratio=1)
        net_table.add_column(ratio=1)

        online_style = t.success if state.network.online else t.danger
        online_str = f"[bold {online_style}]{'Online' if state.network.online else 'Offline'}[/]"

        net_details_l = (
            f"[bold {t.accent}]Host   :[/] {state.network.hostname}\n"
            f"[bold {t.accent}]IP     :[/] {state.network.local_ip}\n"
            f"[bold {t.accent}]Status :[/] {online_str}"
        )
        net_details_r = (
            f"[bold {t.accent}]Upload :[/] {format_bytes(int(state.network.upload_speed))}/s\n"
            f"[bold {t.accent}]Download:[/] {format_bytes(int(state.network.download_speed))}/s\n"
            f"[bold {t.accent}]Transf :[/] TX {format_bytes(state.network.total_sent)} / RX {format_bytes(state.network.total_recv)}"
        )

        net_table.add_row(
            Text.from_markup(net_details_l),
            Text.from_markup(net_details_r)
        )

        # Append speedtest information
        speedtest_status = Text("")
        if state.network.speedtest_running:
            speedtest_status = Text.from_markup(f"\n[bold {t.warning}]Running Speedtest... Please wait.[/]")
        elif state.network.speedtest_download is not None:
            speedtest_status = Text.from_markup(
                f"\n[bold {t.accent}]Speedtest Results -> Download:[/] {state.network.speedtest_download:.1f} Mbps | "
                f"[bold {t.accent}]Upload:[/] {state.network.speedtest_upload:.1f} Mbps"
            )
        else:
            speedtest_status = Text.from_markup(f"\n[dim {t.text}]Press [S] to run Speedtest[/]")

        net_layout = Table.grid(expand=True)
        net_layout.add_row(net_table)
        net_layout.add_row(speedtest_status)

        layout["network"].update(
            Panel(
                net_layout,
                title=f"[bold {t.title}]Network Status[/]",
                border_style=t.border,
            )
        )

        # ------------------ PROCESSES ------------------
        proc_table = Table.grid(expand=True)
        proc_table.add_column(ratio=1)
        proc_table.add_column(ratio=1)

        # CPU Processes Table
        cpu_proc_t = Table(
            box=None,
            header_style=f"bold {t.accent}",
            expand=True,
            padding=(0, 1),
        )
        cpu_proc_t.add_column("PID", ratio=2)
        cpu_proc_t.add_column("Name", ratio=5)
        cpu_proc_t.add_column("CPU %", ratio=3, justify="right")

        for proc in state.top_cpu_processes[:6]:
            cpu_proc_t.add_row(
                str(proc.pid),
                proc.name[:12],
                f"{proc.cpu_percent:.1f}%",
            )

        # RAM Processes Table
        mem_proc_t = Table(
            box=None,
            header_style=f"bold {t.accent}",
            expand=True,
            padding=(0, 1),
        )
        mem_proc_t.add_column("PID", ratio=2)
        mem_proc_t.add_column("Name", ratio=5)
        mem_proc_t.add_column("RAM", ratio=3, justify="right")

        for proc in state.top_mem_processes[:6]:
            mem_proc_t.add_row(
                str(proc.pid),
                proc.name[:12],
                format_bytes(proc.memory_rss),
            )

        proc_table.add_row(
            Panel(cpu_proc_t, title=f"[bold {t.title}]Top CPU[/]", border_style="grey30"),
            Panel(mem_proc_t, title=f"[bold {t.title}]Top Memory[/]", border_style="grey30"),
        )

        layout["processes"].update(
            Panel(
                proc_table,
                title=f"[bold {t.title}]Active Processes[/]",
                border_style=t.border,
            )
        )

        # ------------------ FOOTER ------------------
        # Maintain export notification message for 3 seconds
        if self.export_message and (time.time() - self.export_msg_time > 3.0):
            self.export_message = ""

        left_footer = f"[bold {t.border}]Theme:[/] {self.config.theme.upper()}"
        if self.export_message:
            left_footer += f" | [bold {t.success}]{self.export_message}[/]"

        navigation = (
            f"[bold {t.accent}][Q][/] Quit | "
            f"[bold {t.accent}][R][/] Refresh | "
            f"[bold {t.accent}][T][/] Toggle Theme | "
            f"[bold {t.accent}][E][/] Export Report | "
            f"[bold {t.accent}][S][/] Run Speedtest"
        )
        
        footer_table = Table.grid(expand=True)
        footer_table.add_row(
            Text.from_markup(left_footer),
            Align.right(Text.from_markup(navigation))
        )

        layout["footer"].update(
            Panel(
                footer_table,
                border_style=t.border,
            )
        )

    def run(self) -> None:
        """
        Execute the live monitor user interface and run keyboard listener loop.
        """
        logger.info("Starting Dashboard display...")
        
        layout = self.create_layout()
        
        # Capture first sample
        state = self.monitor.collect()
        self.populate_layout(layout, state)

        # Rich Live rendering block
        with Live(layout, console=self.console, refresh_per_second=2, screen=True) as live:
            with NonBlockingInput() as kb:
                last_refresh = time.time()
                running = True
                
                while running:
                    # Check keyboard events
                    char = kb.get_char()
                    if char is not None:
                        char_upper = char.upper()
                        if char_upper == "Q" or char == "\x03":  # Handle 'q' or Ctrl+C
                           running = False
                           logger.info("Shutdown signal received via keystroke.")
                        elif char_upper == "R":
                            state = self.monitor.collect()
                            self.populate_layout(layout, state)
                            last_refresh = time.time()
                            logger.info("Forced refresh triggered by user.")
                            live.refresh()
                        elif char_upper == "T":
                            self.cycle_theme()
                            self.populate_layout(layout, state)
                            live.refresh()
                        elif char_upper == "E":
                            self.trigger_export(state)
                            self.populate_layout(layout, state)
                            live.refresh()
                        elif char_upper == "S":
                            if state.network.online and not state.network.speedtest_running:
                                self.monitor.network_collector.run_speedtest_async()
                                live.refresh()

                    # Check automatic refresh interval timeout
                    now = time.time()
                    if now - last_refresh >= self.config.refresh_interval:
                        state = self.monitor.collect()
                        self.populate_layout(layout, state)
                        last_refresh = now
                        
                    time.sleep(0.05)  # Tiny pause to reduce CPU consumption in loop
        
        # Auto-export on exit feature
        if self.config.auto_export:
            logger.info("Auto-export enabled. Triggering exit snapshot...")
            self.trigger_export(state)
            print(f"Auto-exported snapshot in format '{self.config.export_format}' to exports/ directory.")
