"""
Test suite for the Terminal System Dashboard Pro.
Tests custom top-level functions in project.py and pure functions in utils.py.
Satisfies CS50P requirements.
"""

import os
import json
import pytest
from typing import Generator

from project import load_config, save_report, validate_theme
from utils import format_bytes, uptime


# ==========================================
# 1. Tests for validate_theme()
# ==========================================

def test_validate_theme_valid() -> None:
    """Test validate_theme with valid and trimmed inputs."""
    assert validate_theme("dark") == "dark"
    assert validate_theme("  light  ") == "light"
    assert validate_theme("CYBERPUNK") == "cyberpunk"
    assert validate_theme("Matrix") == "matrix"
    assert validate_theme("ocean") == "ocean"


def test_validate_theme_invalid() -> None:
    """Test validate_theme with unsupported theme names."""
    with pytest.raises(ValueError, match="Unsupported theme"):
        validate_theme("red")
    with pytest.raises(ValueError, match="Unsupported theme"):
        validate_theme("neon-cyber")
    with pytest.raises(ValueError, match="Unsupported theme"):
        validate_theme("default")


def test_validate_theme_type_error() -> None:
    """Test validate_theme with non-string inputs (edge cases)."""
    with pytest.raises(TypeError, match="Theme name must be a string"):
        validate_theme(123)  # type: ignore
    with pytest.raises(TypeError, match="Theme name must be a string"):
        validate_theme(None)  # type: ignore
    with pytest.raises(TypeError, match="Theme name must be a string"):
        validate_theme([])  # type: ignore


# ==========================================
# 2. Tests for format_bytes()
# ==========================================

def test_format_bytes_valid_binary() -> None:
    """Test format_bytes under binary prefix rules (base 1024)."""
    assert format_bytes(0, use_binary=True) == "0 B"
    assert format_bytes(1023, use_binary=True) == "1023 B"
    assert format_bytes(1024, use_binary=True) == "1.00 KiB"
    assert format_bytes(1536, use_binary=True) == "1.50 KiB"
    assert format_bytes(1048576, use_binary=True) == "1.00 MiB"
    assert format_bytes(1073741824, use_binary=True) == "1.00 GiB"


def test_format_bytes_valid_metric() -> None:
    """Test format_bytes under decimal metric prefix rules (base 1000)."""
    assert format_bytes(0, use_binary=False) == "0 B"
    assert format_bytes(999, use_binary=False) == "999 B"
    assert format_bytes(1000, use_binary=False) == "1.00 KB"
    assert format_bytes(1500, use_binary=False) == "1.50 KB"
    assert format_bytes(1000000, use_binary=False) == "1.00 MB"
    assert format_bytes(1000000000, use_binary=False) == "1.00 GB"


def test_format_bytes_invalid_value() -> None:
    """Test format_bytes with negative numbers (invalid input)."""
    with pytest.raises(ValueError, match="Byte value cannot be negative"):
        format_bytes(-1)
    with pytest.raises(ValueError, match="Byte value cannot be negative"):
        format_bytes(-9999)


def test_format_bytes_edge_cases() -> None:
    """Test format_bytes with extremely large scale numbers."""
    # Exabyte boundary
    large_num = 1024 ** 6
    assert format_bytes(large_num, use_binary=True) == "1.00 EiB"
    
    large_metric = 1000 ** 6
    assert format_bytes(large_metric, use_binary=False) == "1.00 EB"


# ==========================================
# 3. Tests for uptime()
# ==========================================

def test_uptime_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test uptime calculations against mocked system times."""
    # Mock time.time to return 1000.0
    monkeypatch.setattr("time.time", lambda: 1000.0)

    # 1. 10 seconds uptime
    assert uptime(990.0) == "10s"
    
    # 2. 1 minute 5 seconds
    assert uptime(935.0) == "1m 5s"
    
    # 3. 2 hours 5 minutes 12 seconds
    assert uptime(1000.0 - (2 * 3600 + 5 * 60 + 12)) == "2h 5m 12s"

    # 4. 3 days 4 hours 12 minutes 0 seconds
    assert uptime(1000.0 - (3 * 86400 + 4 * 3600 + 12 * 60)) == "3d 4h 12m 0s"


def test_uptime_edge_cases(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test uptime with future or negative time differentials."""
    monkeypatch.setattr("time.time", lambda: 1000.0)

    # Boot time in the future (skewed clock) - should clamp to 0s
    assert uptime(1005.0) == "0s"
    
    # Boot time exactly matches current time
    assert uptime(1000.0) == "0s"


# ==========================================
# 4. Tests for load_config()
# ==========================================

def test_load_config_missing_file() -> None:
    """Test loading configuration when the file does not exist."""
    config = load_config("non_existent_config_file_name.json")
    assert isinstance(config, dict)
    assert config["refresh_interval"] == 1.0
    assert config["theme"] == "dark"


def test_load_config_valid_file(tmp_path: pytest.TempPathFactory) -> None:
    """Test loading configurations from a valid JSON file."""
    # Create temp directory and configuration file
    d = tmp_path
    f = d / "test_config.json"
    
    test_data = {
        "refresh_interval": 2.5,
        "theme": "cyberpunk",
        "units": "metric",
        "auto_export": True,
        "export_format": "csv"
    }
    f.write_text(json.dumps(test_data))

    config = load_config(str(f))
    assert config["refresh_interval"] == 2.5
    assert config["theme"] == "cyberpunk"
    assert config["units"] == "metric"
    assert config["auto_export"] is True
    assert config["export_format"] == "csv"


def test_load_config_invalid_malformed(tmp_path: pytest.TempPathFactory) -> None:
    """Test loading configurations from a malformed JSON file."""
    d = tmp_path
    f = d / "bad_config.json"
    f.write_text("{ malformed json }")

    # Should fall back to standard default configuration keys
    config = load_config(str(f))
    assert config["theme"] == "dark"
    assert config["refresh_interval"] == 1.0


def test_load_config_partial_and_out_of_bounds(tmp_path: pytest.TempPathFactory) -> None:
    """Test loading configs with partial missing fields and extreme values."""
    d = tmp_path
    f = d / "bounds_config.json"
    
    test_data = {
        "refresh_interval": -10.0,  # Below safety threshold (0.1)
        "theme": "unsupported_theme_name",  # Invalid theme
    }
    f.write_text(json.dumps(test_data))

    config = load_config(str(f))
    # Should resolve refresh to 1.0 (failsafe) and theme to dark (default fallback)
    assert config["refresh_interval"] == 1.0
    assert config["theme"] == "dark"
    assert config["units"] == "binary"  # Missing key should default


# ==========================================
# 5. Tests for save_report()
# ==========================================

def test_save_report_success(tmp_path: pytest.TempPathFactory) -> None:
    """Test saving file contents successfully."""
    d = tmp_path
    f = d / "subdir" / "system_report.txt"
    
    content = "System Report Content Text Example"
    success = save_report(content, str(f))
    
    assert success is True
    assert f.exists()
    assert f.read_text() == content


def test_save_report_failures() -> None:
    """Test save_report with invalid inputs or empty values."""
    # 1. Invalid file paths
    assert save_report("content", "") is False
    
    # 2. Invalid content type (edge cases)
    assert save_report(None, "path.txt") is False  # type: ignore
    assert save_report(12345, "path.txt") is False  # type: ignore
