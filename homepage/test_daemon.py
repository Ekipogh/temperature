"""
Tests for the temperature daemon functionality.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

from django.test import TestCase

from homepage.models import Temperature
from homepage.test_utils import MockSwitchBot, MockSwitchBotDevice


class TemperatureDaemonTestCase(TestCase):
    """Base test case for daemon tests."""

    def setUp(self):
        """Set up test environment."""
        # Mock environment variables
        self.env_patcher = patch.dict(
            os.environ,
            {
                "SWITCHBOT_TOKEN": "test_token",
                "SWITCHBOT_SECRET": "test_secret",
                "LIVING_ROOM_MAC": "MAC001",
                "BEDROOM_MAC": "MAC002",
                "OFFICE_MAC": "MAC003",
                "OUTDOOR_MAC": "MAC004",
                "TEMPERATURE_INTERVAL": "60",
            },
        )
        self.env_patcher.start()

        # Create a temporary log file for testing
        self.temp_log = tempfile.NamedTemporaryFile(delete=False, suffix=".log")
        self.temp_log_path = self.temp_log.name
        self.temp_log.close()

    def tearDown(self):
        """Clean up test environment."""
        self.env_patcher.stop()

        # Clean up temporary log file
        try:
            os.unlink(self.temp_log_path)
        except FileNotFoundError:
            pass


class TemperatureDaemonInitializationTests(TemperatureDaemonTestCase):
    """Test daemon initialization."""

    def test_daemon_initialization_success_production(self):
        """Test successful daemon initialization in production environment."""
        # Import here to avoid Django configuration issues
        with patch("scripts.temperature_daemon.django.setup"):
            with patch(
                "scripts.temperature_daemon.SwitchBotService"
            ) as mock_service_class:
                from scripts.temperature_daemon import TemperatureDaemon

                # Mock service
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service

                # Ensure production environment
                with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
                    daemon = TemperatureDaemon()

                # Verify initialization
                self.assertTrue(daemon.running)
                self.assertEqual(daemon.interval, 60)
                self.assertEqual(len(daemon.devices), 4)
                # Verify production service was used
                mock_service_class.assert_called_once()

    def test_daemon_initialization_success_preprod(self):
        """Test successful daemon initialization in preprod environment."""
        # Import here to avoid Django configuration issues
        with patch("scripts.temperature_daemon.django.setup"):
            with patch(
                "scripts.temperature_daemon.PreProdSwitchBotService"
            ) as mock_service_class:
                from scripts.temperature_daemon import TemperatureDaemon

                # Mock service
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service

                # Ensure preprod environment
                with patch.dict(os.environ, {"ENVIRONMENT": "preprod"}):
                    daemon = TemperatureDaemon()

                # Verify initialization
                self.assertTrue(daemon.running)
                self.assertEqual(daemon.interval, 60)
                self.assertEqual(len(daemon.devices), 4)
                # Verify preprod service was used
                mock_service_class.assert_called_once()

    def test_daemon_initialization_missing_credentials(self):
        """Test daemon initialization with missing credentials."""
        # Import here to avoid Django configuration issues
        with patch("scripts.temperature_daemon.django.setup"):
            from scripts.temperature_daemon import TemperatureDaemon

            # Remove credentials from environment
            with patch.dict(os.environ, {}, clear=True):
                with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
                    with patch(
                        "scripts.temperature_daemon.SwitchBotService"
                    ) as mock_service_class:
                        # Mock service to raise ValueError for missing credentials
                        mock_service_class.side_effect = ValueError(
                            "SWITCHBOT_TOKEN and SWITCHBOT_SECRET must be set in environment variables"
                        )

                        with self.assertRaises(ValueError) as context:
                            TemperatureDaemon()

                        self.assertIn(
                            "SWITCHBOT_TOKEN and SWITCHBOT_SECRET must be set",
                            str(context.exception),
                        )

    def test_daemon_initialization_with_default_macs(self):
        """Test daemon initialization with default MAC addresses."""
        # Import here to avoid Django configuration issues
        with patch("scripts.temperature_daemon.django.setup"):
            with patch(
                "scripts.temperature_daemon.SwitchBotService"
            ) as mock_service_class:
                from scripts.temperature_daemon import TemperatureDaemon

                # Mock service
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service

                # Remove all MAC environment variables to test defaults
                with patch.dict(os.environ, {}, clear=True):
                    with patch.dict(
                        os.environ,
                        {
                            "SWITCHBOT_TOKEN": "test_token",
                            "SWITCHBOT_SECRET": "test_secret",
                            "ENVIRONMENT": "production",
                        },
                    ):
                        daemon = TemperatureDaemon()

                # Verify default MAC addresses are used
                expected_devices = {
                    "living_room_thermometer": "D40E84863006",
                    "bedroom_thermometer": "D40E84861814",
                    "office_thermometer": "D628EA1C498F",
                    "outdoor_thermometer": "D40E84064570",
                }
                self.assertEqual(daemon.devices, expected_devices)

    def test_daemon_initialization_with_custom_macs(self):
        """Test daemon initialization with custom MAC addresses from environment."""
        # Import here to avoid Django configuration issues
        with patch("scripts.temperature_daemon.django.setup"):
            with patch(
                "scripts.temperature_daemon.SwitchBotService"
            ) as mock_service_class:
                from scripts.temperature_daemon import TemperatureDaemon

                # Mock service
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service

                # Set custom MAC addresses
                custom_env = {
                    "SWITCHBOT_TOKEN": "test_token",
                    "SWITCHBOT_SECRET": "test_secret",
                    "ENVIRONMENT": "production",
                    "LIVING_ROOM_MAC": "CUSTOM001",
                    "BEDROOM_MAC": "CUSTOM002",
                    "OFFICE_MAC": "CUSTOM003",
                    "OUTDOOR_MAC": "CUSTOM004",
                }

                with patch.dict(os.environ, custom_env):
                    daemon = TemperatureDaemon()

                # Verify custom MAC addresses are used
                expected_devices = {
                    "living_room_thermometer": "CUSTOM001",
                    "bedroom_thermometer": "CUSTOM002",
                    "office_thermometer": "CUSTOM003",
                    "outdoor_thermometer": "CUSTOM004",
                }
                self.assertEqual(daemon.devices, expected_devices)

    def test_device_configuration_structure(self):
        """Test that device configuration has the expected structure."""
        # Import here to avoid Django configuration issues
        with patch("scripts.temperature_daemon.django.setup"):
            with patch(
                "scripts.temperature_daemon.SwitchBotService"
            ) as mock_service_class:
                from scripts.temperature_daemon import TemperatureDaemon

                # Mock service
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service

                daemon = TemperatureDaemon()

                # Verify all expected devices are present
                expected_device_names = {
                    "living_room_thermometer",
                    "bedroom_thermometer",
                    "office_thermometer",
                    "outdoor_thermometer",
                }
                self.assertEqual(set(daemon.devices.keys()), expected_device_names)

                # Verify all MAC addresses are strings
                for device_name, mac_address in daemon.devices.items():
                    self.assertIsInstance(mac_address, str)
                    self.assertTrue(
                        len(mac_address) > 0,
                        f"MAC address for {device_name} should not be empty",
                    )


class TemperatureDaemonDataCollectionTests(TemperatureDaemonTestCase):
    """Test daemon data collection functionality."""

    def setUp(self):
        """Set up daemon for testing."""
        super().setUp()

        # Import and patch here to avoid import issues
        self.django_setup_patcher = patch("scripts.temperature_daemon.django.setup")
        self.django_setup_patcher.start()

        # Import after patching
        from homepage.test_utils import MockSwitchBotService

        # Create mock service with test data
        self.mock_service = MockSwitchBotService()
        self.mock_service.set_device_data("MAC001", 22.5, 65.0)  # Living Room
        self.mock_service.set_device_data("MAC002", 21.0, 58.0)  # Bedroom
        self.mock_service.set_device_data("MAC003", 23.5, 62.0)  # Office
        self.mock_service.set_device_data("MAC004", 15.5, 85.0)  # Outdoor

        # Patch the service classes to return our mock
        self.switchbot_service_patcher = patch(
            "scripts.temperature_daemon.SwitchBotService"
        )
        self.preprod_service_patcher = patch(
            "scripts.temperature_daemon.PreProdSwitchBotService"
        )

        mock_switchbot_service = self.switchbot_service_patcher.start()
        mock_preprod_service = self.preprod_service_patcher.start()

        mock_switchbot_service.return_value = self.mock_service
        mock_preprod_service.return_value = self.mock_service

        # Create daemon with test environment
        with patch.dict(os.environ, {"ENVIRONMENT": "test"}):
            from scripts.temperature_daemon import TemperatureDaemon

            self.daemon = TemperatureDaemon()

    def tearDown(self):
        """Clean up patches."""
        self.switchbot_service_patcher.stop()
        self.preprod_service_patcher.stop()
        self.django_setup_patcher.stop()
        super().tearDown()

    def test_get_temperature_success(self):
        """Test successful temperature reading."""
        temperature = self.daemon.get_temperature("living_room_thermometer")
        self.assertEqual(temperature, 22.5)

    def test_get_humidity_success(self):
        """Test successful humidity reading."""
        humidity = self.daemon.get_humidity("living_room_thermometer")
        self.assertEqual(humidity, 65.0)

    def test_get_temperature_device_not_found(self):
        """Test temperature reading from non-existent device."""
        temperature = self.daemon.get_temperature("nonexistent_device")
        self.assertIsNone(temperature)

    def test_get_temperature_device_failure(self):
        """Test temperature reading when device fails."""
        # Make device fail
        self.mock_service.set_device_failure(
            "MAC001", True, "Device communication error"
        )

        temperature = self.daemon.get_temperature("living_room_thermometer")
        self.assertIsNone(temperature)

    def test_get_temperature_invalid_range(self):
        """Test temperature reading with out-of-range values."""
        # Set invalid temperature
        self.mock_service.set_device_data("MAC001", -60.0, 50.0)

        temperature = self.daemon.get_temperature("living_room_thermometer")
        self.assertIsNone(temperature)

    def test_get_humidity_invalid_range(self):
        """Test humidity reading with out-of-range values."""
        # Set invalid humidity
        self.mock_service.set_device_data("MAC001", 20.0, 150.0)

        humidity = self.daemon.get_humidity("living_room_thermometer")
        self.assertIsNone(humidity)

    def test_get_temperature_auth_error_recovery(self):
        """Test temperature reading with authentication error recovery."""
        # Make service return None to simulate auth error recovery
        self.mock_service.set_device_failure("MAC001", True, "Authentication error")

        # Should return None on auth error
        temperature = self.daemon.get_temperature("living_room_thermometer")
        self.assertIsNone(temperature)

    def test_get_temperature_rate_limit_handling(self):
        """Test temperature reading with rate limit error handling."""
        # Simulate rate limit by making service fail initially
        self.mock_service.set_device_failure("MAC001", True, "Rate limit exceeded")

        # Should return None when rate limited
        temperature = self.daemon.get_temperature("living_room_thermometer")
        self.assertIsNone(temperature)

        # After clearing the failure, should work again
        self.mock_service.set_device_failure("MAC001", False)
        temperature = self.daemon.get_temperature("living_room_thermometer")
        self.assertEqual(temperature, 22.5)

    def test_store_temperature_success(self):
        """Test successful temperature storage."""
        success = self.daemon.store_temperature("living_room_thermometer", 22.5, 65.0)

        self.assertTrue(success)

        # Verify record was created
        temp_record = Temperature.objects.filter(location="Living Room").first()
        self.assertIsNotNone(temp_record)
        if temp_record:
            self.assertEqual(temp_record.temperature, 22.5)
            self.assertEqual(temp_record.humidity, 65.0)

    def test_store_temperature_invalid_type(self):
        """Test temperature storage with invalid data types."""
        # This would raise an exception in real code, but we'll test the behavior
        try:
            success = self.daemon.store_temperature(
                "living_room_thermometer", "invalid_string", 65.0  # type: ignore
            )
            self.assertFalse(success)
        except (TypeError, ValueError):
            # Exception is acceptable for invalid input
            pass

        self.assertEqual(Temperature.objects.count(), 0)

    def test_store_temperature_unknown_device(self):
        """Test temperature storage for unknown device."""
        success = self.daemon.store_temperature("unknown_device", 22.5, 65.0)

        # Should still succeed but log warning
        self.assertTrue(success)

        temp_record = Temperature.objects.first()
        self.assertIsNotNone(temp_record)
        if temp_record:
            self.assertEqual(temp_record.location, "Unknown")


class TemperatureDaemonMainLoopTests(TemperatureDaemonTestCase):
    """Test daemon main loop functionality."""

    def test_daemon_environment_service_selection(self):
        """Test that daemon selects correct service based on environment."""
        with patch("scripts.temperature_daemon.django.setup"):
            from scripts.temperature_daemon import TemperatureDaemon

            # Test production environment
            with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
                with patch(
                    "scripts.temperature_daemon.SwitchBotService"
                ) as mock_service:
                    _ = TemperatureDaemon()
                    mock_service.assert_called_once()

            # Test preprod environment
            with patch.dict(os.environ, {"ENVIRONMENT": "preprod"}):
                with patch(
                    "scripts.temperature_daemon.PreProdSwitchBotService"
                ) as mock_preprod_service:
                    _ = TemperatureDaemon()
                    mock_preprod_service.assert_called_once()

    def test_preprod_service_returns_random_values(self):
        """Test that PreProdSwitchBotService returns random values."""
        with patch("scripts.temperature_daemon.django.setup"):
            from scripts.temperature_daemon import PreProdSwitchBotService

            service = PreProdSwitchBotService()

            # Test multiple calls to ensure randomness
            temps = [service.get_temperature("test_mac") for _ in range(5)]
            humidities = [service.get_humidity("test_mac") for _ in range(5)]

            # All values should be non-None
            self.assertTrue(all(t is not None for t in temps))
            self.assertTrue(all(h is not None for h in humidities))

            # Values should be in expected ranges
            for temp in temps:
                if temp is not None:
                    self.assertGreaterEqual(temp, 18.0)
                    self.assertLessEqual(temp, 25.0)

            for humidity in humidities:
                if humidity is not None:
                    self.assertGreaterEqual(humidity, 30.0)
                    self.assertLessEqual(humidity, 50.0)
