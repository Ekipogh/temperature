import json
import logging
import os
import random
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Load environment variables from .env file
from dotenv import load_dotenv
from switchbot import SwitchBot

import django
from django.utils import timezone

load_dotenv(Path(__file__).parent.parent / ".env")

# Adjust the Python path to include the project directory
project_dir = Path(__file__).parent.parent  # Point to project root
sys.path.append(str(project_dir))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "temperature.settings")
django.setup()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(
        "temperature_daemon.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class SwitchBotService:
    """Service for interacting with SwitchBot devices."""

    def __init__(self):
        self._bot = None

    def connect(self, mac_address: str):
        """Connect to the SwitchBot device."""
        token = os.getenv("SWITCHBOT_TOKEN")
        secret = os.getenv("SWITCHBOT_SECRET")
        if not token or not secret:
            raise ValueError(
                "SWITCHBOT_TOKEN and SWITCHBOT_SECRET must be set in environment variables")
        if not self._bot:
            self._bot = SwitchBot(token=token, secret=secret)
        device = self._bot.device(id=mac_address)
        return device

    def get_temperature(self, mac_address: str) -> Optional[float]:
        """Get temperature reading from the device."""
        try:
            device = self.connect(mac_address)
            status = device.status()
            temp_value = status.get("temperature")
            if temp_value is None:
                return None
            temperature = float(temp_value)
            return temperature
        except Exception as e:
            logger.error(f"Error getting temperature from {mac_address}: {e}")
            return None

    def get_humidity(self, mac_address: str) -> Optional[float]:
        """Get humidity reading from the device."""
        try:
            device = self.connect(mac_address)
            status = device.status()
            humidity_value = status.get("humidity")
            if humidity_value is None:
                return None
            humidity = float(humidity_value)
            return humidity
        except Exception as e:
            logger.error(f"Error getting humidity from {mac_address}: {e}")
            return None


class PreProdSwitchBotService(SwitchBotService):
    def get_temperature(self, mac_address: str) -> float | None:
        # return random temperature for pre-prod testing
        return round(random.uniform(18.0, 25.0), 2)

    def get_humidity(self, mac_address: str) -> float | None:
        # return random humidity for pre-prod testing
        return round(random.uniform(30.0, 50.0), 2)


class TemperatureDaemon:
    """A daemon to periodically read temperature from SwitchBot devices and store it in the Django database."""

    def __init__(self):
        self.running = True
        # Increased default interval to 10 minutes (600 seconds) to be API-friendly
        self.interval = int(
            os.getenv("TEMPERATURE_INTERVAL", "600"))  # seconds

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
        self.status_file = Path(__file__).parent.parent / "daemon_status.json"
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
        }

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        is_preprod = os.getenv(
            "ENVIRONMENT", "production").lower() == "preprod"
        # Initialize SwitchBot service
        if is_preprod:
            self.switchbot_service = PreProdSwitchBotService()
        else:
            self.switchbot_service = SwitchBotService()

        # Initialize devices (now all required attributes are available)
        self._init_devices()

        logger.info(
            f"TemperatureDaemon initialized with {len(self.devices)} devices")

    def _init_devices(self):
        """Initialize all temperature devices with retry logic for rate limiting."""
        # Device configuration - can be moved to environment variables if needed
        device_configs = {
            "living_room_thermometer": os.getenv("LIVING_ROOM_MAC", "D40E84863006"),
            "bedroom_thermometer": os.getenv("BEDROOM_MAC", "D40E84861814"),
            "office_thermometer": os.getenv("OFFICE_MAC", "D628EA1C498F"),
            "outdoor_thermometer": os.getenv("OUTDOOR_MAC", "D40E84064570"),
        }

        self.devices = {}
        successful_devices = 0

        for device_name, mac_address in device_configs.items():
            max_attempts = 5  # Maximum attempts for device initialization
            attempt = 0

            while attempt < max_attempts and self.running:
                try:
                    # Store device MAC address for SwitchBotService to use
                    self.devices[device_name] = mac_address
                    logger.info(
                        f"Initialized device: {device_name} ({mac_address})")
                    successful_devices += 1
                    break  # Success, move to next device

                except Exception as e:
                    attempt += 1
                    error_str = str(e).lower()

                    # Check for rate limiting (HTTP 429)
                    if "429" in str(e) or "rate limit" in error_str:
                        if attempt < max_attempts:
                            logger.warning(
                                f"Rate limit during device initialization for {device_name} (attempt {attempt}/{max_attempts})"
                            )
                            self._handle_rate_limit_error(
                                f"device initialization for {device_name}"
                            )
                            continue  # Retry after backoff
                        else:
                            logger.error(
                                f"Failed to initialize device {device_name} after {max_attempts} attempts due to rate limiting"
                            )
                            break
                    else:
                        # Non-rate-limit error
                        logger.error(
                            f"Failed to initialize device {device_name} (attempt {attempt}/{max_attempts}): {e}"
                        )
                        if attempt < max_attempts:
                            # Short delay for non-rate-limit errors
                            time.sleep(5)
                        break  # Don't retry non-rate-limit errors

        # Reset rate limit state if we had any successful device initializations
        if successful_devices > 0:
            self._reset_rate_limit_state()

        # Handle the case where no devices were initialized
        if not self.devices:
            logger.error(
                "No devices were successfully initialized after retries")
            logger.info(
                "Daemon will continue running and retry device initialization in the main loop"
            )
            # Don't crash - let the daemon continue and try again later

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
                    "iteration_count": self.iteration_counter,
                    "consecutive_failures": consecutive_failures,
                    "uptime_seconds": int(uptime),
                    "pid": os.getpid(),
                }
            )

            if successful_reading:
                self.status["last_successful_reading"] = current_time.isoformat()
                self.last_successful_reading = current_time

            # Write status to file
            with open(self.status_file, "w") as f:
                json.dump(self.status, f, indent=2)

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
                temperature = self.switchbot_service.get_temperature(
                    mac_address)

                if temperature is None:
                    logger.warning(
                        f"No temperature reading from {device_name}")
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

                # Handle authentication errors
                elif "401" in str(e) or "authentication" in error_str:
                    logger.warning(
                        f"Authentication error for {device_name}, reinitializing SwitchBot service"
                    )
                    try:
                        self.switchbot_service = SwitchBotService()
                        # Don't retry here, let the next iteration handle it
                        return None
                    except Exception as init_e:
                        logger.error(
                            f"Failed to reinitialize SwitchBot service after auth error: {init_e}"
                        )
                        return None
                else:
                    # Other errors - log and return None
                    logger.error(
                        f"Error reading temperature from {device_name}: {e}")
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

                # Handle authentication errors
                elif "401" in str(e) or "authentication" in error_str:
                    logger.warning(
                        f"Authentication error for {device_name}, reinitializing SwitchBot service"
                    )
                    try:
                        self.switchbot_service = SwitchBotService()
                        # Don't retry here, let the next iteration handle it
                        return None
                    except Exception as init_e:
                        logger.error(
                            f"Failed to reinitialize SwitchBot service after auth error: {init_e}"
                        )
                        return None
                else:
                    # Other errors - log and return None
                    logger.error(
                        f"Error reading humidity from {device_name}: {e}")
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
        logger.info(
            f"Starting temperature daemon with {self.interval}s interval")

        consecutive_failures = 0
        max_consecutive_failures = 5

        try:
            while self.running:
                self.iteration_counter += 1
                logger.info(
                    f"--- Daemon iteration {self.iteration_counter} ---")

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
                        logger.error(
                            f"Error during device re-initialization: {e}")

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
                    logger.warning(
                        f"Complete cycle failure #{consecutive_failures}")

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
