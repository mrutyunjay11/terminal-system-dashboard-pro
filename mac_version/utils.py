"""
Utility module for the Terminal System Dashboard Pro.
Contains helper functions for data formatting, mathematical conversions, and system validation.
"""

import time
import socket
import logging
from typing import Callable, Any

logger = logging.getLogger("Utils")


def format_bytes(n: int, use_binary: bool = True) -> str:
    """
    Format a byte count into a human-readable string with units.

    Args:
        n (int): The number of bytes to format. Must be non-negative.
        use_binary (bool): If True, uses binary prefixes (KiB, MiB, etc. base 1024).
                           If False, uses metric prefixes (KB, MB, etc. base 1000).

    Returns:
        str: Human-readable byte representation.

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("Byte value cannot be negative.")

    factor = 1024.0 if use_binary else 1000.0
    suffixes = (
        ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB"]
        if use_binary
        else ["B", "KB", "MB", "GB", "TB", "PB", "EB"]
    )

    val = float(n)
    for suffix in suffixes:
        if val < factor:
            if suffix == "B":
                return f"{int(val)} B"
            return f"{val:.2f} {suffix}"
        val /= factor

    return f"{val:.2f} {suffixes[-1]}"


def uptime(boot_time: float) -> str:
    """
    Calculate and format uptime from system boot time.

    Args:
        boot_time (float): System boot timestamp (seconds since epoch).

    Returns:
        str: Human-readable uptime formatted as 'Xd Xh Xm Xs'.
    """
    current_time = time.time()
    diff = current_time - boot_time
    if diff < 0:
        diff = 0.0

    days = int(diff // 86400)
    hours = int((diff % 86400) // 3600)
    minutes = int((diff % 3600) // 60)
    seconds = int(diff % 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0 or days > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")

    return " ".join(parts)


def check_internet_connection(host: str = "8.8.8.8", port: int = 53, timeout: float = 1.0) -> bool:
    """
    Perform a lightweight socket connection check to confirm internet connectivity.

    Args:
        host (str): IP address of target host (default Google DNS).
        port (int): Port of target host (default DNS).
        timeout (float): Connection timeout in seconds.

    Returns:
        bool: True if connection succeeded, False otherwise.
    """
    try:
        # Use a socket connection instead of subprocess ping (which is slow and OS-dependent)
        socket.setdefaulttimeout(timeout)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
        return True
    except (socket.timeout, OSError):
        return False


def get_local_ip() -> str:
    """
    Retrieve the primary local IP address of the current machine.

    Returns:
        str: Local IP address string or '127.0.0.1' if offline.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not actually establish a connection; useful for finding local IP interface
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        s.close()
    return local_ip


def safe_execute(default_return: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to safely execute functions, catching exceptions and logging them.

    Args:
        default_return (Any): The fallback value to return if the function crashes.

    Returns:
        Callable: Decorator wrapper.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error("Exception in %s: %s", func.__name__, e, exc_info=True)
                return default_return
        return wrapper
    return decorator
