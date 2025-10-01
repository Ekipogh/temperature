from switchbot import SwitchBot
from pathlib import Path
import os
import sys
import time
import django
from django.utils import timezone
import logging
import signal
from typing import Optional, Dict, Any

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

# Adjust the Python path to include the project directory
project_dir = Path(__file__).parent.parent  # Point to project root
sys.path.append(str(project_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'temperature.settings')
django.setup()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('temperature_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TemperatureDaemon:
    '''A daemon to periodically read temperature from SwitchBot devices and store it in the Django database.'''

    def __init__(self):
        self.running = True
        self.interval = int(os.getenv("TEMPERATURE_INTERVAL", "60"))  # seconds

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Initialize SwitchBot connection
        self._init_switchbot()

        # Initialize devices
        self._init_devices()

        self.iteration_counter = 0

        logger.info(
            f"TemperatureDaemon initialized with {len(self.devices)} devices")

    def _init_switchbot(self):
        """Initialize SwitchBot connection with proper error handling."""
        token = os.getenv("SWITCHBOT_TOKEN")
        secret = os.getenv("SWITCHBOT_SECRET")

        if not token or not secret:
            raise ValueError(
                "SWITCHBOT_TOKEN and SWITCHBOT_SECRET must be set in environment variables")

        try:
            self._bot = SwitchBot(token=token, secret=secret)
            logger.info("SwitchBot connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SwitchBot: {e}")
            raise

    def _init_devices(self):
        """Initialize all temperature devices."""
        # Device configuration - can be moved to environment variables if needed
        device_configs = {
            "living_room_thermometer": os.getenv("LIVING_ROOM_MAC", "D40E84863006"),
            "bedroom_thermometer": os.getenv("BEDROOM_MAC", "D40E84861814"),
            "office_thermometer": os.getenv("OFFICE_MAC", "D628EA1C498F"),
            "outdoor_thermometer": os.getenv("OUTDOOR_MAC", "D40E84064570")
        }

        self.devices = {}

        for device_name, mac_address in device_configs.items():
            try:
                device = self._bot.device(id=mac_address)
                self.devices[device_name] = device
                logger.info(
                    f"Initialized device: {device_name} ({mac_address})")
            except Exception as e:
                logger.error(f"Failed to initialize device {device_name}: {e}")
                # Continue with other devices rather than failing completely

        if not self.devices:
            raise RuntimeError("No devices were successfully initialized")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def get_temperature(self, device_name) -> Optional[float]:
        """Get temperature reading from a device with error handling and validation."""
        device = self.devices.get(device_name)
        if not device:
            logger.error(f"Device {device_name} not found")
            return None

        try:
            status = device.status()
            temperature = float(status.get("temperature"))

            if temperature is None:
                logger.warning(f"No temperature reading from {device_name}")
                return None

            # Validate temperature range (reasonable for indoor/outdoor temps)
            if not (-50 <= temperature <= 70):
                logger.warning(
                    f"Invalid temperature reading from {device_name}: {temperature}°C")
                return None

            return temperature

        except Exception as e:
            logger.error(f"Error reading temperature from {device_name}: {e}")
            
            # Check if it's an authentication error
            if "401" in str(e) or "authentication" in str(e).lower():
                logger.warning(f"Authentication error for {device_name}, reinitializing SwitchBot connection")
                try:
                    self._init_switchbot()
                    self._init_devices()
                    # Retry once after reinitialization
                    device = self.devices.get(device_name)
                    if device:
                        status = device.status()
                        temperature = float(status.get("temperature"))
                        if temperature is not None and (-50 <= temperature <= 70):
                            return temperature
                except Exception as retry_e:
                    logger.error(f"Retry failed for {device_name}: {retry_e}")
            
            return None

    def get_humidity(self, device_name) -> Optional[float]:
        """Get humidity reading from a device with error handling and validation."""
        device = self.devices.get(device_name)
        if not device:
            logger.error(f"Device {device_name} not found")
            return None

        try:
            status = device.status()
            humidity = float(status.get("humidity"))

            if humidity is None:
                logger.warning(f"No humidity reading from {device_name}")
                return None

            # Validate humidity range (0-100%)
            if not (0 <= humidity <= 100):
                logger.warning(
                    f"Invalid humidity reading from {device_name}: {humidity}%")
                return None

            return humidity

        except Exception as e:
            logger.error(f"Error reading humidity from {device_name}: {e}")
            
            # Check if it's an authentication error
            if "401" in str(e) or "authentication" in str(e).lower():
                logger.warning(f"Authentication error for {device_name}, reinitializing SwitchBot connection")
                try:
                    self._init_switchbot()
                    self._init_devices()
                    # Retry once after reinitialization
                    device = self.devices.get(device_name)
                    if device:
                        status = device.status()
                        humidity = float(status.get("humidity"))
                        if humidity is not None and (0 <= humidity <= 100):
                            return humidity
                except Exception as retry_e:
                    logger.error(f"Retry failed for {device_name}: {retry_e}")
            
            return None

    def store_temperature(self, device_name: str, temperature: float, humidity: float) -> bool:
        """Store temperature reading in database with error handling and validation."""
        try:
            # Import here to avoid circular import issues
            from homepage.models import Temperature
            from django.db import transaction

            # Validate inputs
            if not isinstance(temperature, (int, float)):
                logger.error(
                    f"Invalid temperature type for {device_name}: {type(temperature)}")
                return False

            if humidity is not None and not isinstance(humidity, (int, float)):
                logger.error(
                    f"Invalid humidity type for {device_name}: {type(humidity)}")
                return False

            location_map = {
                "living_room_thermometer": "Living Room",
                "bedroom_thermometer": "Bedroom",
                "office_thermometer": "Office",
                "outdoor_thermometer": "Outdoor"
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
                    timestamp=timezone.now()
                )
                # Validate model before saving
                temperature_record.full_clean()
                temperature_record.save()

            logger.info(
                f"Stored temperature {temperature}°C for {location}, humidity {humidity}%")
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
                logger.info(f"--- Daemon iteration {self.iteration_counter} ---")
                
                cycle_success = False

                for device_name in self.devices.keys():
                    try:
                        temperature = self.get_temperature(device_name)
                        humidity = self.get_humidity(device_name) or 0

                        if temperature is not None:
                            success = self.store_temperature(
                                device_name, temperature,
                                humidity=humidity)
                            if success:
                                cycle_success = True
                        else:
                            logger.warning(
                                f"Skipping storage for {device_name} due to invalid reading")

                    except Exception as e:
                        logger.error(
                            f"Unexpected error processing {device_name}: {e}")

                # Track consecutive failures
                if cycle_success:
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    logger.warning(
                        f"Complete cycle failure #{consecutive_failures}")

                    if consecutive_failures >= max_consecutive_failures:
                        logger.critical(
                            f"Too many consecutive failures ({consecutive_failures}), stopping daemon")
                        break

                # Sleep between cycles
                if self.running:
                    time.sleep(self.interval)

        except KeyboardInterrupt:
            logger.info("Daemon interrupted by user")
        except Exception as e:
            logger.critical(f"Fatal error in daemon main loop: {e}")
        finally:
            logger.info("Temperature daemon stopped")


if __name__ == "__main__":
    daemon = TemperatureDaemon()
    daemon.run()
