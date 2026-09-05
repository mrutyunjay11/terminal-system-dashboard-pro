"""
Theme configurations module for the Terminal System Dashboard Pro.
Defines style palettes for different dashboard modes (Dark, Light, Cyberpunk, Matrix, Ocean).
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ThemeColors:
    """
    Implements color and style bindings for dashboard components.
    
    Attributes:
        border (str): Color of panel borders.
        title (str): Color of panel/section headers.
        text (str): General text color.
        accent (str): Secondary highlights/values color.
        success (str): Normal status or high battery color.
        warning (str): Medium warning color.
        danger (str): High alert/error color.
        bar_complete (str): Color of filled portions in progress bars.
        bar_remaining (str): Color of empty portions in progress bars.
    """
    border: str
    title: str
    text: str
    accent: str
    success: str
    warning: str
    danger: str
    bar_complete: str
    bar_remaining: str


# Palette Definitions
THEMES: Dict[str, ThemeColors] = {
    "dark": ThemeColors(
        border="cyan",
        title="bold white",
        text="white",
        accent="cyan",
        success="green",
        warning="yellow",
        danger="red",
        bar_complete="bright_cyan",
        bar_remaining="grey30",
    ),
    "light": ThemeColors(
        border="blue",
        title="bold black",
        text="black",
        accent="blue",
        success="dark_green",
        warning="dark_goldenrod",
        danger="red",
        bar_complete="blue",
        bar_remaining="grey85",
    ),
    "cyberpunk": ThemeColors(
        border="magenta",
        title="bold yellow",
        text="bright_cyan",
        accent="bright_magenta",
        success="bright_green",
        warning="bright_yellow",
        danger="bright_red",
        bar_complete="bright_magenta",
        bar_remaining="grey19",
    ),
    "matrix": ThemeColors(
        border="green",
        title="bold bright_green",
        text="green",
        accent="bright_green",
        success="bright_green",
        warning="dark_green",
        danger="red",
        bar_complete="green",
        bar_remaining="grey15",
    ),
    "ocean": ThemeColors(
        border="blue",
        title="bold bright_cyan",
        text="cyan",
        accent="deep_sky_blue1",
        success="green",
        warning="yellow",
        danger="red",
        bar_complete="deep_sky_blue1",
        bar_remaining="grey27",
    ),
}


def validate_theme(theme_name: str) -> str:
    """
    Validate if a given theme name exists in the database.

    Args:
        theme_name (str): Theme name to validate.

    Returns:
        str: Sanitized lowercase theme name.

    Raises:
        ValueError: If theme_name is not supported.
    """
    if not isinstance(theme_name, str):
        raise TypeError("Theme name must be a string.")

    normalized = theme_name.strip().lower()
    if normalized not in THEMES:
        raise ValueError(
            f"Invalid theme: '{theme_name}'. Supported themes are: {', '.join(THEMES.keys())}"
        )
    return normalized


def get_theme(theme_name: str) -> ThemeColors:
    """
    Retrieve style configurations for a specific theme.

    Args:
        theme_name (str): Theme name (e.g. 'dark', 'cyberpunk').

    Returns:
        ThemeColors: The theme specification object.
    """
    try:
        valid_name = validate_theme(theme_name)
        return THEMES[valid_name]
    except (ValueError, TypeError):
        # Graceful fallback to dark theme
        return THEMES["dark"]
