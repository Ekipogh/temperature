import json
import logging
import os
import random
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

# Load environment variables from .env file
from dotenv import load_dotenv

import django
from django.utils import timezone

load_dotenv(Path(__file__).parent.parent / ".env")

# Adjust the Python path to include the project directory
project_dir = Path(__file__).parent.parent  # Point to project root
sys.path.append(str(project_dir))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "temperature.settings")
django.setup()

# Import shared services
from services.switchbot_service import get_device_configs, get_switchbot_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("temperature_daemon.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class TemperatureDaemon:
    """A daemon to periodically read temperature from SwitchBot devices and store it in the Django database."""

    def __init__(self):
        self.running = True
        # Increased default interval to 10 minutes (600 seconds) to be API-friendly
        self.interval = int(os.getenv("TEMPERATURE_INTERVAL", "600"))  # seconds

        # Increased rate limit sleep to 5 minutes to avoid hitting API limits
        self.rate_limit_sleep_time = int(
            os.getenv("RATE_LIMIT_SLEEP_TIME", "300")
        )  # seconds

        # Initialize retry state BEFORE device initialization
        self.rate_limit_retry_count = 0
        self.max_retry_interval = 24 * 60 * 60  # 24 hours in seconds
        self.base_retry_interval = 60  # Start with 1 minute
        self.last_rate_limit_time = None

        # Initialize status tracking BEFORE device initialization
        self.iteration_counter = 0
        self.status_file = Path(
            os.getenv(
                "DAEMON_STATUS_FILE",
                Path(__file__).parent.parent / "daemon_status.json",
            )
        )
        self.last_successful_reading = None
        self.start_time = datetime.now()

        self.status = {
            "status": "starting",
            "last_check": None,
            "last_successful_reading": None,
            "total_readings": 0,
            "error_count": 0,
            "current_error": None,
            "uptime_seconds": 0,
            "next_check_in": self.interval,
            "daemon_pid": os.getpid(),
            "iteration_counter": 0,
            "temperature_device_status": "unknown",
            "humidity_device_status": "unknown",
            "api_rate_limited": False,
            "rate_limit_retry_count": 0,
            "last_rate_limit_time": None,
            "retry_interval": None,
            "update_interval": self.interval,
            "hub_connectivity": {
                "hub_ping": None,
                "api_connectivity": None,
                "overall_healthy": None,
                "last_check": None,
            },
        }

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Initialize SwitchBot service using shared factory
        self.switchbot_service = get_switchbot_service()

        # Initialize devices (now all required attributes are available)
        self._init_devices()

        logger.info(f"TemperatureDaemon initialized with {len(self.devices)} devices")

    def _check_hub_connectivity(self, hub_ip: Optional[str] = None) -> bool:
        """Check if SwitchBot hub is reachable on local network via ping."""
        # Default hub IP - you should configure this for your network
        if not hub_ip:
            hub_ip = os.getenv("SWITCHBOT_HUB_IP", "192.168.1.100")  # Configure this

        try:
            # Use ping command appropriate for the OS
            if os.name == "nt":  # Windows
                result = subprocess.run(
                    ["ping", "-n", "1", "-w", "3000", hub_ip],  # 3 second timeout
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
            else:  # Linux/Mac
                result = subprocess.run(
                    ["ping", "-c", "1", "-W", "3", hub_ip],  # 3 second timeout
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

            is_reachable = result.returncode == 0

            if is_reachable:
                logger.debug(f"SwitchBot hub at {hub_ip} is reachable")
            else:
                logger.warning(f"SwitchBot hub at {hub_ip} is not reachable")

            return is_reachable

        except subprocess.TimeoutExpired:
            logger.warning(f"Ping to SwitchBot hub {hub_ip} timed out")
            return False
        except Exception as e:
            logger.error(f"Error pinging SwitchBot hub {hub_ip}: {e}")
            return False

    def _check_hub_api_connectivity(self) -> bool:
        """Check SwitchBot API connectivity by making a simple API call."""
        try:
            # Try to get status from the first available device - lightweight check
            if not self.devices:
                logger.warning("No devices configured for API connectivity check")
                return False

            test_device = next(iter(self.devices.keys()))
            mac_address = self.devices[test_device]

            # Make a quick status call to test API connectivity
            device = self.switchbot_service.connect(mac_address)
            status = device.status()

            if status is not None:
                logger.debug(f"SwitchBot API is responsive (tested with {test_device})")
                return True
            else:
                logger.warning("SwitchBot API returned no status")
                return False

        except Exception as e:
            error_str = str(e).lower()

            if "429" in str(e) or "rate limit" in error_str:
                logger.warning("SwitchBot API rate limited (API is working)")
                return True  # Rate limit means API is working, just restricted
            elif "401" in str(e) or "authentication" in error_str:
                logger.warning("SwitchBot API authentication issue")
                return True  # Auth issue means API is reachable
            elif "timeout" in error_str or "connection" in error_str:
                logger.error(f"SwitchBot API connectivity issue: {e}")
                return False
            else:
                logger.error(f"Unknown SwitchBot API error: {e}")
                return False

    def _perform_connectivity_checks(self) -> Dict[str, Union[bool, None]]:
        """Perform comprehensive connectivity checks for SwitchBot hub and API."""
        results: Dict[str, Union[bool, None]] = {
            "hub_ping": False,
            "api_connectivity": False,
            "overall_healthy": False,
        }

        try:
            # Check hub network connectivity
            hub_ip = os.getenv("SWITCHBOT_HUB_IP")
            if hub_ip:
                results["hub_ping"] = self._check_hub_connectivity(hub_ip)
            else:
                logger.info("SWITCHBOT_HUB_IP not configured, skipping ping check")
                results["hub_ping"] = None  # Unknown state

            # Check API connectivity
            results["api_connectivity"] = self._check_hub_api_connectivity()

            # Overall health assessment
            if results["hub_ping"] is None:
                # If ping check is not configured, base health on API only
                results["overall_healthy"] = results["api_connectivity"]
            else:
                # Both ping and API should be working for full health
                results["overall_healthy"] = (
                    results["hub_ping"] and results["api_connectivity"]
                )

            # Log connectivity status
            if results["overall_healthy"]:
                logger.debug("SwitchBot connectivity: All systems healthy")
            else:
                status_msg = []
                if results["hub_ping"] is False:
                    status_msg.append("Hub unreachable")
                if not results["api_connectivity"]:
                    status_msg.append("API unresponsive")
                logger.warning(
                    f"SwitchBot connectivity issues: {', '.join(status_msg)}"
                )

            return results

        except Exception as e:
            logger.error(f"Error during connectivity checks: {e}")
            return results

    def _init_devices(self):
        """Initialize device configuration by storing MAC addresses."""
        # Use shared device configuration
        self.devices = get_device_configs()

        logger.info(
            f"Configured {len(self.devices)} devices: {list(self.devices.keys())}"
        )

    def _update_status(
        self, consecutive_failures: int = 0, successful_reading: bool = False
    ):
        """Update the daemon status file for monitoring."""
        try:
            current_time = datetime.now()
            uptime = (current_time - self.start_time).total_seconds()

            self.status.update(
                {
                    "running": self.running,
                    "last_update": current_time.isoformat(),
                    "iteration_counter": self.iteration_counter,
                    "consecutive_failures": consecutive_failures,
                    "uptime_seconds": int(uptime),
                    "pid": os.getpid(),
                }
            )

            if successful_reading:
                self.status["last_successful_reading"] = current_time.isoformat()
                self.last_successful_reading = current_time

            # Write status to file
            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(self.status, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to update status file: {e}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        # Update status to indicate shutdown
        self.status["running"] = False
        self._update_status()

    def _calculate_retry_delay(self) -> int:
        """Calculate exponential backoff delay with jitter for rate limiting."""
        if self.rate_limit_retry_count == 0:
            return self.base_retry_interval

        # Exponential backoff: base * (2^retry_count) with max cap
        delay = min(
            self.base_retry_interval * (2**self.rate_limit_retry_count),
            self.max_retry_interval,
        )

        # Add jitter (±25%) to avoid thundering herd
        jitter = delay * 0.25
        delay = delay + random.uniform(-jitter, jitter)

        return int(max(delay, self.base_retry_interval))

    def _handle_rate_limit_error(self, context: str = "API call") -> bool:
        """Handle rate limiting with exponential backoff."""
        self.rate_limit_retry_count += 1
        retry_delay = self._calculate_retry_delay()
        self.last_rate_limit_time = datetime.now()

        # Update status with retry information
        self.status["rate_limit_retry_count"] = self.rate_limit_retry_count
        self.status["next_retry_interval"] = retry_delay
        self._update_status()

        logger.warning(
            f"Rate limit error during {context}. "
            f"Retry #{self.rate_limit_retry_count}, waiting {retry_delay} seconds. "
            f"Next attempt at {(datetime.now().timestamp() + retry_delay)}"
        )

        # Check if we've hit the maximum retry interval (24 hours)
        if retry_delay >= self.max_retry_interval:
            logger.critical(
                f"Reached maximum retry interval of {self.max_retry_interval} seconds (24 hours). "
                f"API rate limiting may be severe."
            )

        # Sleep for the calculated delay
        time.sleep(retry_delay)
        return True

    def _reset_rate_limit_state(self):
        """Reset rate limiting state after successful API call."""
        if self.rate_limit_retry_count > 0:
            logger.info(
                f"API call successful after {self.rate_limit_retry_count} rate limit retries"
            )
            self.rate_limit_retry_count = 0
            self.status["rate_limit_retry_count"] = 0
            self.status["next_retry_interval"] = None
            self._update_status()

    def get_temperature(self, device_name) -> Optional[float]:
        """Get temperature reading from a device with error handling and validation."""
        mac_address = self.devices.get(device_name)
        if not mac_address:
            logger.error(f"Device {device_name} not found")
            return None

        max_attempts = 3  # Maximum retry attempts for data collection

        for attempt in range(max_attempts):
            try:
                temperature = self.switchbot_service.get_temperature(mac_address)

                if temperature is None:
                    logger.warning(f"No temperature reading from {device_name}")
                    return None

                # Validate temperature range (reasonable for indoor/outdoor temps)
                if not (-50 <= temperature <= 70):
                    logger.warning(
                        f"Invalid temperature reading from {device_name}: {temperature}°C"
                    )
                    return None

                # Success - reset rate limit state if this was after retries
                if attempt > 0:
                    self._reset_rate_limit_state()

                return temperature

            except Exception as e:
                error_str = str(e).lower()

                # Handle rate limiting with exponential backoff
                if "429" in str(e) or "rate limit" in error_str:
                    if attempt < max_attempts - 1:  # Don't retry on last attempt
                        logger.warning(
                            f"Rate limit during temperature reading for {device_name} (attempt {attempt + 1}/{max_attempts})"
                        )
                        self._handle_rate_limit_error(
                            f"temperature reading for {device_name}"
                        )
                        continue  # Retry after backoff
                    else:
                        logger.error(
                            f"Failed to get temperature from {device_name} after {max_attempts} attempts due to rate limiting"
                        )
                        return None

                # Handle authentication errors - service handles retry internally
                elif "401" in str(e) or "authentication" in error_str:
                    logger.warning(
                        f"Authentication error for {device_name} - service will handle retry"
                    )
                    return None
                else:
                    # Other errors - log and return None
                    logger.error(f"Error reading temperature from {device_name}: {e}")
                    return None

        return None

    def get_humidity(self, device_name) -> Optional[float]:
        """Get humidity reading from a device with error handling and validation."""
        mac_address = self.devices.get(device_name)
        if not mac_address:
            logger.error(f"Device {device_name} not found")
            return None

        max_attempts = 3  # Maximum retry attempts for data collection

        for attempt in range(max_attempts):
            try:
                humidity = self.switchbot_service.get_humidity(mac_address)

                if humidity is None:
                    logger.warning(f"No humidity reading from {device_name}")
                    return None

                # Validate humidity range (0-100%)
                if not (0 <= humidity <= 100):
                    logger.warning(
                        f"Invalid humidity reading from {device_name}: {humidity}%"
                    )
                    return None

                # Success - reset rate limit state if this was after retries
                if attempt > 0:
                    self._reset_rate_limit_state()

                return humidity

            except Exception as e:
                error_str = str(e).lower()

                # Handle rate limiting with exponential backoff
                if "429" in str(e) or "rate limit" in error_str:
                    if attempt < max_attempts - 1:  # Don't retry on last attempt
                        logger.warning(
                            f"Rate limit during humidity reading for {device_name} (attempt {attempt + 1}/{max_attempts})"
                        )
                        self._handle_rate_limit_error(
                            f"humidity reading for {device_name}"
                        )
                        continue  # Retry after backoff
                    else:
                        logger.error(
                            f"Failed to get humidity from {device_name} after {max_attempts} attempts due to rate limiting"
                        )
                        return None

                # Handle authentication errors - service handles retry internally
                elif "401" in str(e) or "authentication" in error_str:
                    logger.warning(
                        f"Authentication error for {device_name} - service will handle retry"
                    )
                    return None
                else:
                    # Other errors - log and return None
                    logger.error(f"Error reading humidity from {device_name}: {e}")
                    return None

        return None

    def store_temperature(
        self, device_name: str, temperature: float, humidity: float
    ) -> bool:
        """Store temperature reading in database with error handling and validation."""
        try:
            # Import here to avoid circular import issues
            from django.db import transaction

            from homepage.models import Temperature

            # Validate inputs
            if not isinstance(temperature, (int, float)):
                logger.error(
                    f"Invalid temperature type for {device_name}: {type(temperature)}"
                )
                return False

            if humidity is not None and not isinstance(humidity, (int, float)):
                logger.error(
                    f"Invalid humidity type for {device_name}: {type(humidity)}"
                )
                return False

            location_map = {
                "living_room_thermometer": "Living Room",
                "bedroom_thermometer": "Bedroom",
                "office_thermometer": "Office",
                "outdoor_thermometer": "Outdoor",
            }

            location = location_map.get(device_name, "Unknown")

            if location == "Unknown":
                logger.warning(f"Unknown device name: {device_name}")

            # Use atomic transaction for data integrity
            with transaction.atomic():
                temperature_record = Temperature(
                    location=location,
                    temperature=temperature,
                    humidity=humidity,
                    timestamp=timezone.now(),
                )
                # Validate model before saving
                temperature_record.full_clean()
                temperature_record.save()

            logger.info(
                f"Stored temperature {temperature}°C for {location}, humidity {humidity}%"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to store temperature for {device_name}: {e}")
            return False

    def run(self):
        """Main daemon loop with comprehensive error handling."""
        logger.info(f"Starting temperature daemon with {self.interval}s interval")

        consecutive_failures = 0
        max_consecutive_failures = 5

        try:
            while self.running:
                self.iteration_counter += 1
                logger.info(f"--- Daemon iteration {self.iteration_counter} ---")

                # Check if we have devices, if not try to initialize them
                if not self.devices:
                    logger.warning(
                        "No devices available, attempting to re-initialize..."
                    )
                    try:
                        self._init_devices()
                        if not self.devices:
                            logger.warning(
                                "Device re-initialization failed, will retry next cycle"
                            )
                    except Exception as e:
                        logger.error(f"Error during device re-initialization: {e}")

                # Perform connectivity checks periodically (every 5 iterations or on first run)
                if self.iteration_counter == 1 or self.iteration_counter % 5 == 0:
                    logger.info("Performing SwitchBot connectivity checks...")
                    connectivity_results = self._perform_connectivity_checks()

                    # Update status with connectivity information
                    self.status["hub_connectivity"].update(connectivity_results)
                    self.status["hub_connectivity"][
                        "last_check"
                    ] = datetime.now().isoformat()

                    # Log connectivity status
                    if not connectivity_results["overall_healthy"]:
                        logger.warning(
                            f"SwitchBot connectivity issues detected: "
                            f"Hub ping: {connectivity_results['hub_ping']}, "
                            f"API: {connectivity_results['api_connectivity']}"
                        )
                    else:
                        logger.info("SwitchBot connectivity: All systems healthy")

                cycle_success = False

                # Only try to collect data if we have devices
                if self.devices:
                    for device_name in self.devices.keys():
                        try:
                            temperature = self.get_temperature(device_name)
                            humidity = self.get_humidity(device_name) or 0

                            if temperature is not None:
                                success = self.store_temperature(
                                    device_name, temperature, humidity=humidity
                                )
                                if success:
                                    cycle_success = True
                            else:
                                logger.warning(
                                    f"Skipping storage for {device_name} due to invalid reading"
                                )

                        except Exception as e:
                            logger.error(
                                f"Unexpected error processing {device_name}: {e}"
                            )
                else:
                    logger.warning("No devices available for data collection")

                # Track consecutive failures
                if cycle_success:
                    consecutive_failures = 0
                elif not self.devices:
                    # Don't count device initialization failures as harshly
                    # since they're usually due to rate limiting and recoverable
                    logger.warning(
                        "No devices available - will retry initialization next cycle"
                    )
                else:
                    consecutive_failures += 1
                    logger.warning(f"Complete cycle failure #{consecutive_failures}")

                    if consecutive_failures >= max_consecutive_failures:
                        logger.critical(
                            f"Too many consecutive failures ({consecutive_failures}), stopping daemon"
                        )
                        self.running = False
                        break

                # Update status
                self._update_status(consecutive_failures, cycle_success)

                # Sleep between cycles
                if self.running:
                    time.sleep(self.interval)

        except KeyboardInterrupt:
            logger.info("Daemon interrupted by user")
        except Exception as e:
            logger.critical(f"Fatal error in daemon main loop: {e}")
        finally:
            self.running = False
            self.status["running"] = False
            self._update_status()
            logger.info("Temperature daemon stopped")


if __name__ == "__main__":
    daemon = TemperatureDaemon()
    daemon.run()
