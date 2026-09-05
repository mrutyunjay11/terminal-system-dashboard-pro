"""
Network metrics collection module for the Terminal System Dashboard Pro.
Tracks network interface throughput, IP configurations, internet status, and handles speedtests.
"""

import time
import socket
import logging
import threading
import psutil
import speedtest
from dataclasses import dataclass
from typing import Optional
from utils import get_local_ip, check_internet_connection, safe_execute

logger = logging.getLogger("Network")


@dataclass
class NetworkData:
    """
    Dataclass representing collected Network metrics and optional Speedtest results.
    """
    hostname: str
    local_ip: str
    online: bool
    upload_speed: float  # Bytes per second
    download_speed: float  # Bytes per second
    total_sent: int  # Cumulative bytes sent
    total_recv: int  # Cumulative bytes received
    speedtest_download: Optional[float] = None  # Megabits per second
    speedtest_upload: Optional[float] = None  # Megabits per second
    speedtest_running: bool = False


class NetworkCollector:
    """
    Measures current upload/download rates and queries local/internet connection states.
    Hosts an asynchronous worker thread for running full bandwidth speedtests on request.
    """

    def __init__(self) -> None:
        """Initialize interface stat history trackers."""
        logger.info("Initializing Network Collector...")
        self._prev_io = self._get_net_io()
        self._prev_time: float = time.time()
        self._hostname: str = socket.gethostname()

        # Speedtest states
        self.speedtest_download: Optional[float] = None
        self.speedtest_upload: Optional[float] = None
        self._speedtest_running: bool = False

    @safe_execute(None)
    def _get_net_io(self) -> getattr(psutil, "net_io_counters", None):
        """Safely fetch global network IO packets counter."""
        return psutil.net_io_counters()

    def run_speedtest_async(self) -> None:
        """Spawn a background thread to calculate internet speed without blocking UI."""
        if self._speedtest_running:
            logger.warning("Speedtest is already running in the background.")
            return

        self._speedtest_running = True
        self.speedtest_download = None
        self.speedtest_upload = None
        
        logger.info("Spawning background thread for speedtest...")
        thread = threading.Thread(target=self._speedtest_worker, daemon=True)
        thread.start()

    def _speedtest_worker(self) -> None:
        """Core execution worker for speedtest calculation."""
        try:
            # Initialize speedtest engine
            st = speedtest.Speedtest(secure=True)
            st.get_best_server()
            
            logger.info("Running speedtest download check...")
            download_bps = st.download()
            
            logger.info("Running speedtest upload check...")
            upload_bps = st.upload()

            self.speedtest_download = float(download_bps / 1_000_000.0)  # Convert to Mbps
            self.speedtest_upload = float(upload_bps / 1_000_000.0)
            logger.info("Speedtest completed successfully: DL=%s Mbps, UL=%s Mbps", 
                        self.speedtest_download, self.speedtest_upload)
        except Exception as e:
            logger.error("Speedtest execution failed: %s", e)
        finally:
            self._speedtest_running = False

    def collect(self) -> NetworkData:
        """
        Gather real-time network settings and calculate instantaneous upload/download speed.

        Returns:
            NetworkData: The populated Network metrics dataclass.
        """
        current_io = self._get_net_io()
        current_time = time.time()

        upload_speed = 0.0
        download_speed = 0.0
        total_sent = 0
        total_recv = 0

        if current_io:
            total_sent = current_io.bytes_sent
            total_recv = current_io.bytes_recv

            if self._prev_io:
                time_delta = current_time - self._prev_time
                if time_delta > 0.05:
                    sent_diff = current_io.bytes_sent - self._prev_io.bytes_sent
                    recv_diff = current_io.bytes_recv - self._prev_io.bytes_recv
                    upload_speed = max(0.0, float(sent_diff / time_delta))
                    download_speed = max(0.0, float(recv_diff / time_delta))

        # Update monitoring window
        self._prev_io = current_io
        self._prev_time = current_time

        # Network lookup states
        local_ip = get_local_ip()
        online = check_internet_connection()

        return NetworkData(
            hostname=self._hostname,
            local_ip=local_ip,
            online=online,
            upload_speed=upload_speed,
            download_speed=download_speed,
            total_sent=total_sent,
            total_recv=total_recv,
            speedtest_download=self.speedtest_download,
            speedtest_upload=self.speedtest_upload,
            speedtest_running=self._speedtest_running,
        )
