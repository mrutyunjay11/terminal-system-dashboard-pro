"""
Configuration management module for the Terminal System Dashboard Pro.
Handles loading, saving, and validation of user settings from a JSON file.
"""

import os
import json
import logging
from dataclasses import dataclass, asdict
from typing import Any

# Ensure logs directory exists at the root of the project
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "dashboard.log")

# Configure logger for the application
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("Config")


@dataclass
class AppConfig:
    """
    Dataclass representing application configurations.
    
    Attributes:
        refresh_interval (float): Interval in seconds between dashboard refreshes.
        theme (str): Visual theme name (dark, light, cyberpunk, matrix, ocean).
        units (str): Size unit format (binary for GiB/MiB, metric for GB/MB).
        auto_export (bool): True if system stats should be auto-exported on exit or interval.
        export_format (str): The format for exporting reports (json, csv, txt).
    """
    refresh_interval: float = 1.0
    theme: str = "dark"
    units: str = "binary"
    auto_export: bool = False
    export_format: str = "json"

    def to_dict(self) -> dict[str, Any]:
        """Convert the dataclass instance to a dictionary."""
        return asdict(self)


def get_config_path(filename: str = "config.json") -> str:
    """
    Get the absolute path to the configuration file.

    Args:
        filename (str): The name of the configuration file. Default is 'config.json'.

    Returns:
        str: Absolute file path to the configuration file.
    """
    return os.path.join(PROJECT_ROOT, filename)


def load_config(path: str = "config.json") -> AppConfig:
    """
    Load configurations from a JSON file, falling back to default values on failure.

    Args:
        path (str): Relative or absolute path to the config file.

    Returns:
        AppConfig: Config object with validated settings.
    """
    full_path = get_config_path(path)
    if not os.path.exists(full_path):
        logger.warning("Configuration file not found at %s. Using default settings.", full_path)
        return AppConfig()

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate entries and set defaults if missing/invalid
        refresh_interval = float(data.get("refresh_interval", 1.0))
        if refresh_interval <= 0.1:
            refresh_interval = 1.0  # Minimum safety boundary

        theme = str(data.get("theme", "dark")).lower()
        if theme not in ["dark", "light", "cyberpunk", "matrix", "ocean"]:
            theme = "dark"

        units = str(data.get("units", "binary")).lower()
        if units not in ["binary", "metric"]:
            units = "binary"

        auto_export = bool(data.get("auto_export", False))

        export_format = str(data.get("export_format", "json")).lower()
        if export_format not in ["json", "csv", "txt"]:
            export_format = "json"

        logger.info("Configuration loaded successfully from %s", full_path)
        return AppConfig(
            refresh_interval=refresh_interval,
            theme=theme,
            units=units,
            auto_export=auto_export,
            export_format=export_format,
        )

    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.error("Failed to parse configuration file %s: %s. Using defaults.", full_path, e)
        return AppConfig()
    except PermissionError as e:
        logger.error("Permission denied reading configuration file %s: %s. Using defaults.", full_path, e)
        return AppConfig()


def save_config(config: AppConfig, path: str = "config.json") -> bool:
    """
    Save the application configuration to a JSON file.

    Args:
        config (AppConfig): Configuration object to save.
        path (str): Relative or absolute path to save the config.

    Returns:
        bool: True if save succeeded, False otherwise.
    """
    full_path = get_config_path(path)
    try:
        # Prevent configuration corruption by ensuring root directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2)
        logger.info("Configuration saved successfully to %s", full_path)
        return True
    except (TypeError, PermissionError, OSError) as e:
        logger.error("Failed to write configuration file to %s: %s", full_path, e)
        return False
