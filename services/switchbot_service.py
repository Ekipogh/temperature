import os
import random
import logging
from typing import Dict, Optional
from switchbot import SwitchBot

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
                "SWITCHBOT_TOKEN and SWITCHBOT_SECRET must be set in environment variables"
            )
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

    def get_device_status(self, mac_address: str) -> Optional[Dict]:
        """Get full device status including temperature and humidity."""
        try:
            device = self.connect(mac_address)
            status = device.status()
            return status
        except Exception as e:
            logger.error(f"Error getting status from {mac_address}: {e}")
            return None


class PreProdSwitchBotService(SwitchBotService):
    """Pre-production service that returns random data for testing."""

    def get_temperature(self, mac_address: str) -> Optional[float]:
        """Return random temperature for pre-prod testing."""
        return round(random.uniform(18.0, 25.0), 2)

    def get_humidity(self, mac_address: str) -> Optional[float]:
        """Return random humidity for pre-prod testing."""
        return round(random.uniform(30.0, 50.0), 2)

    def get_device_status(self, mac_address: str) -> Optional[Dict]:
        """Return random device status for pre-prod testing."""
        return {
            "temperature": self.get_temperature(mac_address),
            "humidity": self.get_humidity(mac_address),
            "battery": random.randint(80, 100),
        }


def get_switchbot_service() -> SwitchBotService:
    """Factory function to get the appropriate SwitchBot service based on environment."""
    is_preprod = os.getenv("ENVIRONMENT", "production").lower() == "preprod"

    if is_preprod:
        logger.info("🛠️ Using pre-production SwitchBot service")
        return PreProdSwitchBotService()
    else:
        logger.info("🔌 Using production SwitchBot service")
        return SwitchBotService()


def get_device_configs() -> Dict[str, str]:
    """Get device configuration from environment variables."""
    return {
        "living_room_thermometer": os.getenv("LIVING_ROOM_MAC", "D40E84863006"),
        "bedroom_thermometer": os.getenv("BEDROOM_MAC", "D40E84861814"),
        "office_thermometer": os.getenv("OFFICE_MAC", "D628EA1C498F"),
        "outdoor_thermometer": os.getenv("OUTDOOR_MAC", "D40E84064570"),
    }


def get_location_mac_mapping() -> Dict[str, str]:
    """Get a mapping of human-readable location names to MAC addresses."""
    device_configs = get_device_configs()
    return {
        "Living Room": device_configs["living_room_thermometer"],
        "Bedroom": device_configs["bedroom_thermometer"],
        "Office": device_configs["office_thermometer"],
        "Outdoor": device_configs["outdoor_thermometer"],
    }