"""
Main entry point for the Terminal System Dashboard Pro.
Contains argument parsing, initializations, and standard CS50P top-level functions.
"""

import sys
import time
import argparse
import os
import json
import subprocess
import platform
from typing import Dict, Any

from config import AppConfig, get_config_path
from dashboard import Dashboard
from monitor import SystemMonitor
from export import Exporter

# Setup ASCII banner
ASCII_LOGO = """
████████╗ ██████╗ ██████╗ ██████╗ 
╚══██╔══╝██╔════╝ ██╔══██╗██╔══██╗
   ██║   ╚█████╗  ██║  ██║██████╔╝
   ██║    ╚═══██╗ ██║  ██║██╔═══╝ 
   ██║   ██████╔╝██████╔╝ ██║     
   ╚═╝   ╚═════╝ ╚═════╝  ╚═╝     

  TERMINAL SYSTEM DASHBOARD PRO
"""


def load_config(filepath: str) -> Dict[str, Any]:
    """
    Load configurations from a JSON file. Returns a dict with validated parameters.
    Satisfies CS50P requirements.

    Args:
        filepath (str): Absolute or relative path to the json file.

    Returns:
        Dict[str, Any]: Parsed configuration values.
    """
    defaults = {
        "refresh_interval": 1.0,
        "theme": "dark",
        "units": "binary",
        "auto_export": False,
        "export_format": "json",
    }

    if not filepath or not os.path.exists(filepath):
        return defaults

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        result = {}
        
        # Interval check
        try:
            val = float(data.get("refresh_interval", defaults["refresh_interval"]))
            result["refresh_interval"] = val if val > 0.1 else 1.0
        except (ValueError, TypeError):
            result["refresh_interval"] = 1.0

        # Theme validation
        theme = str(data.get("theme", defaults["theme"])).strip().lower()
        try:
            result["theme"] = validate_theme(theme)
        except ValueError:
            result["theme"] = defaults["theme"]

        # Unit validation
        units = str(data.get("units", defaults["units"])).strip().lower()
        result["units"] = units if units in ["binary", "metric"] else defaults["units"]

        # Auto-export toggle
        result["auto_export"] = bool(data.get("auto_export", defaults["auto_export"]))

        # Export format validation
        fmt = str(data.get("export_format", defaults["export_format"])).strip().lower()
        result["export_format"] = fmt if fmt in ["json", "csv", "txt"] else defaults["export_format"]

        return result
    except (json.JSONDecodeError, PermissionError, OSError):
        return defaults


def save_report(content: str, filepath: str) -> bool:
    """
    Write report content to a given file path. Returns True on success, False on failure.
    Satisfies CS50P requirements.

    Args:
        content (str): The text content of the report.
        filepath (str): Target path to write report file.

    Returns:
        bool: True if write succeeded, False otherwise.
    """
    if not filepath or not isinstance(content, str):
        return False

    try:
        # Create any parent directories if missing
        dir_name = os.path.dirname(filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except (PermissionError, OSError):
        return False


def validate_theme(theme_name: str) -> str:
    """
    Verify if the theme name matches supported visual options.
    Satisfies CS50P requirements.

    Args:
        theme_name (str): Theme name to test.

    Returns:
        str: Valid lowercase theme string.

    Raises:
        ValueError: If theme option is invalid.
        TypeError: If theme_name is not a string.
    """
    if not isinstance(theme_name, str):
        raise TypeError("Theme name must be a string.")

    cleaned = theme_name.strip().lower()
    valid_themes = ["dark", "light", "cyberpunk", "matrix", "ocean"]
    if cleaned not in valid_themes:
        raise ValueError(
            f"Unsupported theme '{theme_name}'. Supported options are: {', '.join(valid_themes)}"
        )
    return cleaned


def main() -> None:
    """
    Main orchestrator for command-line interface execution and dashboard loading.
    """
    parser = argparse.ArgumentParser(
        description="Terminal System Dashboard Pro - Modular real-time monitoring dashboard for developers."
    )
    parser.add_argument(
        "--theme",
        type=str,
        help="Visual theme profile (dark, light, cyberpunk, matrix, ocean). Overrides config.json settings.",
    )
    parser.add_argument(
        "--refresh",
        type=float,
        help="Telemetry polling frequency in seconds (>= 0.1). Overrides config.json settings.",
    )
    parser.add_argument(
        "--export",
        type=str,
        choices=["json", "csv", "txt"],
        help="Compile and export a single report snapshot instantly in the chosen format, then exit.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Print a single system state scan directly to stdout, then exit.",
    )

    args = parser.parse_args()

    # Load file based configuration values
    config_path = get_config_path("config.json")
    config_dict = load_config(config_path)

    # Instantiate AppConfig settings object
    app_config = AppConfig(
        refresh_interval=config_dict["refresh_interval"],
        theme=config_dict["theme"],
        units=config_dict["units"],
        auto_export=config_dict["auto_export"],
        export_format=config_dict["export_format"],
    )

    # Apply CLI argument overrides
    if args.theme:
        try:
            app_config.theme = validate_theme(args.theme)
        except (ValueError, TypeError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    if args.refresh is not None:
        if args.refresh < 0.1:
            print("Error: Refresh interval must be at least 0.1 seconds.", file=sys.stderr)
            sys.exit(1)
        app_config.refresh_interval = args.refresh

    # 1. Instant Export Mode
    if args.export:
        print(f"Gathering telemetry for instant export (Format: {args.export.upper()})...")
        monitor = SystemMonitor()
        state = monitor.collect()
        exporter = Exporter()
        try:
            filepath = exporter.export(state, args.export)
            print(f"Success! Report saved to: {filepath}")
            sys.exit(0)
        except Exception as e:
            print(f"Error exporting report: {e}", file=sys.stderr)
            sys.exit(1)

    # 2. Print Once Mode
    if args.once:
        print("Collecting system metrics snapshot...")
        monitor = SystemMonitor()
        state = monitor.collect()
        exporter = Exporter()
        
        # Format as TXT dynamically using temporary file
        temp_filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_once_report.txt")
        try:
            exporter.export(state, "txt")
            # The exporter writes system_report_<timestamp>.txt, let's find it or print manually to avoid file pollution
            # Actually, let's print a beautiful text representation directly to stdout
            print(ASCII_LOGO)
            print(f"OS Platform    : {state.os.system} {state.os.release} ({state.os.machine})")
            print(f"Hostname       : {state.network.hostname}")
            print(f"Local IP       : {state.network.local_ip}")
            print(f"CPU Model      : {state.cpu.model}")
            print(f"CPU Load (Avg) : {state.cpu.usage_overall:.1f}%")
            print(f"RAM Usage      : {state.memory.ram_percent:.1f}%")
            print(f"Uptime         : {state.os.uptime_str}")
            print(f"Plugged In     : {'Yes' if state.battery.power_plugged else 'No'}")
            sys.exit(0)
        except Exception as e:
            print(f"Error compiling single snapshot: {e}", file=sys.stderr)
            sys.exit(1)

    # 3. Live Dashboard Mode
    try:
        # Visual startup animation
        print(ASCII_LOGO)

        # Cache sudo credentials for die-level temperature reading (Apple Silicon)
        if sys.platform == "darwin" and platform.machine() == "arm64":
            print("Requesting sudo access for CPU/GPU die temperature sensors...")
            print("(Enter your password below — this enables thermal monitoring)")
            print()
            sudo_result = subprocess.run(
                ["sudo", "-v"],
                timeout=60,
            )
            if sudo_result.returncode == 0:
                print("\nSudo access granted. Die temperatures will be available.")
            else:
                print("\nSudo not granted. Using battery sensor fallback for temperature.")
            print()

        print("Initializing monitoring sensors...")
        time.sleep(0.5)

        dashboard = Dashboard(app_config)
        dashboard.run()
    except KeyboardInterrupt:
        print("\nShutdown signal caught. Exiting gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal application failure: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
