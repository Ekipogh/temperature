"""
Test utilities and fixtures for the temperature monitoring system.
"""

from datetime import timedelta
from typing import Optional
from unittest.mock import MagicMock

from django.utils import timezone

from homepage.models import Temperature


class MockSwitchBotService:
    """Mock SwitchBot service for testing."""

    def __init__(self):
        self.temperature_values = {}
        self.humidity_values = {}
        self.should_fail = {}
        self.failure_messages = {}

    def get_temperature(self, mac_address: str) -> Optional[float]:
        """Get mock temperature reading."""
        if self.should_fail.get(mac_address, False):
            return None
        return self.temperature_values.get(mac_address)

    def get_humidity(self, mac_address: str) -> Optional[float]:
        """Get mock humidity reading."""
        if self.should_fail.get(mac_address, False):
            return None
        return self.humidity_values.get(mac_address)

    def get_device_status(self, mac_address: str) -> Optional[dict]:
        """Get mock device status including temperature and humidity."""
        if self.should_fail.get(mac_address, False):
            return None

        temperature = self.temperature_values.get(mac_address)
        humidity = self.humidity_values.get(mac_address)

        if temperature is None and humidity is None:
            return None

        return {
            "temperature": temperature,
            "humidity": humidity,
            "battery": 85,  # Mock battery level
        }

    def set_device_data(
        self, mac_address: str, temperature: Optional[float], humidity: Optional[float]
    ):
        """Set mock data for a device."""
        self.temperature_values[mac_address] = temperature
        self.humidity_values[mac_address] = humidity

    def set_device_failure(
        self, mac_address: str, should_fail: bool = True, message: str = "Mock failure"
    ):
        """Configure a device to fail."""
        self.should_fail[mac_address] = should_fail
        self.failure_messages[mac_address] = message


class MockTestSwitchBotService(MockSwitchBotService):
    """Test service that returns None by default (for testing failure scenarios)."""

    def get_temperature(self, mac_address: str) -> Optional[float]:
        return None

    def get_humidity(self, mac_address: str) -> Optional[float]:
        return None

    def get_device_status(self, mac_address: str) -> Optional[dict]:
        return None


class TemperatureTestMixin:
    """Mixin class providing common test utilities for temperature tests."""

    @staticmethod
    def create_test_temperature(
        location="Test Location", temperature=20.0, humidity=50.0, timestamp=None
    ):
        """Create a test temperature record with default values."""
        if timestamp is None:
            timestamp = timezone.now()

        return Temperature.objects.create(
            timestamp=timestamp,
            location=location,
            temperature=temperature,
            humidity=humidity,
        )

    @staticmethod
    def create_temperature_series(
        location, count=5, base_temperature=20.0, base_humidity=50.0, interval_minutes=5
    ):
        """Create a series of temperature readings for testing."""
        temperatures = []
        base_time = timezone.now()

        for i in range(count):
            temp = Temperature.objects.create(
                timestamp=base_time - timedelta(minutes=i * interval_minutes),
                location=location,
                temperature=base_temperature + i,
                humidity=base_humidity + i if base_humidity else None,
            )
            temperatures.append(temp)

        return temperatures

    @staticmethod
    def create_multi_location_data():
        """Create test data for multiple locations."""
        locations = ["Living Room", "Bedroom", "Office", "Outdoor"]
        temperatures = []
        base_time = timezone.now()

        for i, location in enumerate(locations):
            # Create current reading
            temp = Temperature.objects.create(
                timestamp=base_time - timedelta(minutes=i),
                location=location,
                temperature=20.0 + i * 2,
                humidity=50.0 + i * 5,
            )
            temperatures.append(temp)

            # Create some historical data
            for j in range(1, 4):
                historical_temp = Temperature.objects.create(
                    timestamp=base_time - timedelta(hours=j, minutes=i),
                    location=location,
                    temperature=20.0 + i * 2 - j,
                    humidity=50.0 + i * 5 - j * 2,
                )
                temperatures.append(historical_temp)

        return temperatures


class MockSwitchBotDevice:
    """Mock SwitchBot device for testing."""

    def __init__(
        self,
        temperature="22.5",
        humidity="65",
        battery=85,
        device_id="TEST123",
        device_type="wo_io_sensor",
    ):
        self.temperature = temperature
        self.humidity = humidity
        self.battery = battery
        self.device_id = device_id
        self.device_type = device_type
        self._should_fail = False
        self._failure_message = "Mock device error"

    def status(self):
        """Return mock device status."""
        if self._should_fail:
            raise Exception(self._failure_message)

        return {
            "version": "V0.9",
            "temperature": self.temperature,
            "battery": self.battery,
            "humidity": self.humidity,
            "device_id": self.device_id,
            "device_type": self.device_type,
        }

    def set_failure(self, should_fail=True, message="Mock device error"):
        """Configure the mock device to fail."""
        self._should_fail = should_fail
        self._failure_message = message


class MockSwitchBot:
    """Mock SwitchBot class for testing."""

    def __init__(self, token=None, secret=None):
        self.token = token
        self.secret = secret
        self.devices = {}
        self._should_fail_auth = False

    def device(self, id):
        """Return a mock device."""
        if self._should_fail_auth:
            raise Exception("SwitchBot API server returns status 401")

        if id in self.devices:
            return self.devices[id]

        # Return a default mock device
        return MockSwitchBotDevice(device_id=id)

    def add_device(self, device_id, mock_device):
        """Add a mock device to the SwitchBot instance."""
        self.devices[device_id] = mock_device

    def set_auth_failure(self, should_fail=True):
        """Configure the mock to fail authentication."""
        self._should_fail_auth = should_fail


# Test data constants
SAMPLE_TEMPERATURE_DATA = [
    {
        "location": "Living Room",
        "temperature": 22.5,
        "humidity": 65.0,
        "timestamp": None,  # Will be set to timezone.now() when used
    },
    {"location": "Bedroom", "temperature": 21.0, "humidity": 58.0, "timestamp": None},
    {"location": "Office", "temperature": 23.5, "humidity": 62.0, "timestamp": None},
    {"location": "Outdoor", "temperature": 15.5, "humidity": 85.0, "timestamp": None},
]

INVALID_TEMPERATURE_DATA = [
    {
        "temperature": -60.0,  # Too low
        "location": "Test",
        "humidity": 50.0,
        "error": "temperature_too_low",
    },
    {
        "temperature": 80.0,  # Too high
        "location": "Test",
        "humidity": 50.0,
        "error": "temperature_too_high",
    },
    {
        "temperature": 20.0,
        "location": "Test",
        "humidity": -5.0,  # Too low
        "error": "humidity_too_low",
    },
    {
        "temperature": 20.0,
        "location": "Test",
        "humidity": 105.0,  # Too high
        "error": "humidity_too_high",
    },
    {
        "temperature": 20.0,
        "location": "   ",  # Empty location
        "humidity": 50.0,
        "error": "empty_location",
    },
]
