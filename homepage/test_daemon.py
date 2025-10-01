"""
Tests for the temperature daemon functionality.
"""

import os
import tempfile
from unittest.mock import patch, MagicMock, call
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from homepage.models import Temperature
from homepage.test_utils import MockSwitchBot, MockSwitchBotDevice


class TemperatureDaemonTestCase(TestCase):
    """Base test case for daemon tests."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'SWITCHBOT_TOKEN': 'test_token',
            'SWITCHBOT_SECRET': 'test_secret',
            'LIVING_ROOM_MAC': 'MAC001',
            'BEDROOM_MAC': 'MAC002',
            'OFFICE_MAC': 'MAC003',
            'OUTDOOR_MAC': 'MAC004',
            'TEMPERATURE_INTERVAL': '60'
        })
        self.env_patcher.start()
        
        # Create a temporary log file for testing
        self.temp_log = tempfile.NamedTemporaryFile(delete=False, suffix='.log')
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
    
    @patch('scripts.temperature_daemon.SwitchBot')
    def test_daemon_initialization_success(self, mock_switchbot_class):
        """Test successful daemon initialization."""
        from scripts.temperature_daemon import TemperatureDaemon
        
        # Mock SwitchBot and devices
        mock_switchbot = MockSwitchBot()
        mock_switchbot_class.return_value = mock_switchbot
        
        # Create daemon
        daemon = TemperatureDaemon()
        
        # Verify initialization
        self.assertTrue(daemon.running)
        self.assertEqual(daemon.interval, 60)
        self.assertEqual(len(daemon.devices), 4)
        
        # Verify SwitchBot was initialized with correct credentials
        mock_switchbot_class.assert_called_once_with(
            token='test_token',
            secret='test_secret'
        )
    
    @patch('scripts.temperature_daemon.SwitchBot')
    def test_daemon_initialization_missing_credentials(self, mock_switchbot_class):
        """Test daemon initialization with missing credentials."""
        from scripts.temperature_daemon import TemperatureDaemon
        
        # Remove credentials from environment
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                TemperatureDaemon()
            
            self.assertIn("SWITCHBOT_TOKEN and SWITCHBOT_SECRET must be set", 
                         str(context.exception))
    
    @patch('scripts.temperature_daemon.SwitchBot')
    def test_daemon_initialization_switchbot_failure(self, mock_switchbot_class):
        """Test daemon initialization when SwitchBot fails."""
        from scripts.temperature_daemon import TemperatureDaemon
        
        # Mock SwitchBot to raise an exception
        mock_switchbot_class.side_effect = Exception("SwitchBot connection failed")
        
        with self.assertRaises(Exception) as context:
            TemperatureDaemon()
        
        self.assertIn("SwitchBot connection failed", str(context.exception))
    
    @patch('scripts.temperature_daemon.SwitchBot')
    def test_daemon_device_initialization_partial_failure(self, mock_switchbot_class):
        """Test daemon when some devices fail to initialize."""
        from scripts.temperature_daemon import TemperatureDaemon
        
        # Mock SwitchBot
        mock_switchbot = MagicMock()
        mock_switchbot_class.return_value = mock_switchbot
        
        # Make some devices fail
        def device_side_effect(id):
            if id == 'MAC002':  # Bedroom device fails
                raise Exception("Device not found")
            return MockSwitchBotDevice(device_id=id)
        
        mock_switchbot.device.side_effect = device_side_effect
        
        # Create daemon - should succeed with 3 devices
        daemon = TemperatureDaemon()
        
        self.assertEqual(len(daemon.devices), 3)
        self.assertNotIn('bedroom_thermometer', daemon.devices)
    
    @patch('scripts.temperature_daemon.SwitchBot')
    def test_daemon_all_devices_fail(self, mock_switchbot_class):
        """Test daemon when all devices fail to initialize."""
        from scripts.temperature_daemon import TemperatureDaemon
        
        # Mock SwitchBot
        mock_switchbot = MagicMock()
        mock_switchbot_class.return_value = mock_switchbot
        mock_switchbot.device.side_effect = Exception("No devices available")
        
        with self.assertRaises(RuntimeError) as context:
            TemperatureDaemon()
        
        self.assertIn("No devices were successfully initialized", 
                     str(context.exception))


class TemperatureDaemonDataCollectionTests(TemperatureDaemonTestCase):
    """Test daemon data collection functionality."""
    
    def setUp(self):
        """Set up daemon for testing."""
        super().setUp()
        
        # Import and patch here to avoid import issues
        self.switchbot_patcher = patch('scripts.temperature_daemon.SwitchBot')
        self.mock_switchbot_class = self.switchbot_patcher.start()
        
        from scripts.temperature_daemon import TemperatureDaemon
        
        # Create mock devices
        self.mock_switchbot = MockSwitchBot()
        self.mock_switchbot_class.return_value = self.mock_switchbot
        
        # Add mock devices
        device_configs = {
            'MAC001': MockSwitchBotDevice(temperature='22.5', humidity='65'),
            'MAC002': MockSwitchBotDevice(temperature='21.0', humidity='58'),
            'MAC003': MockSwitchBotDevice(temperature='23.5', humidity='62'),
            'MAC004': MockSwitchBotDevice(temperature='15.5', humidity='85')
        }
        
        for device_id, device in device_configs.items():
            self.mock_switchbot.add_device(device_id, device)
        
        self.daemon = TemperatureDaemon()
    
    def tearDown(self):
        """Clean up patches."""
        self.switchbot_patcher.stop()
        super().tearDown()
    
    def test_get_temperature_success(self):
        """Test successful temperature reading."""
        temperature = self.daemon.get_temperature('living_room_thermometer')
        self.assertEqual(temperature, 22.5)
    
    def test_get_humidity_success(self):
        """Test successful humidity reading."""
        humidity = self.daemon.get_humidity('living_room_thermometer')
        self.assertEqual(humidity, 65.0)
    
    def test_get_temperature_device_not_found(self):
        """Test temperature reading from non-existent device."""
        temperature = self.daemon.get_temperature('nonexistent_device')
        self.assertIsNone(temperature)
    
    def test_get_temperature_device_failure(self):
        """Test temperature reading when device fails."""
        # Make device fail
        device = self.mock_switchbot.devices['MAC001']
        device.set_failure(True, "Device communication error")
        
        temperature = self.daemon.get_temperature('living_room_thermometer')
        self.assertIsNone(temperature)
    
    def test_get_temperature_invalid_range(self):
        """Test temperature reading with out-of-range values."""
        # Create device with invalid temperature
        invalid_device = MockSwitchBotDevice(temperature='-60.0', humidity='50')
        self.mock_switchbot.add_device('INVALID_MAC', invalid_device)
        self.daemon.devices['invalid_thermometer'] = invalid_device
        
        temperature = self.daemon.get_temperature('invalid_thermometer')
        self.assertIsNone(temperature)
    
    def test_get_humidity_invalid_range(self):
        """Test humidity reading with out-of-range values."""
        # Create device with invalid humidity
        invalid_device = MockSwitchBotDevice(temperature='20.0', humidity='150.0')
        self.mock_switchbot.add_device('INVALID_MAC', invalid_device)
        self.daemon.devices['invalid_thermometer'] = invalid_device
        
        humidity = self.daemon.get_humidity('invalid_thermometer')
        self.assertIsNone(humidity)
    
    def test_get_temperature_auth_error_retry(self):
        """Test temperature reading with authentication error and retry."""
        # First call fails with auth error, second succeeds
        device = self.mock_switchbot.devices['MAC001']
        call_count = 0
        
        def status_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("SwitchBot API server returns status 401")
            return {'temperature': '22.5', 'humidity': '65'}
        
        device.status = status_side_effect
        
        # Should retry and succeed
        temperature = self.daemon.get_temperature('living_room_thermometer')
        self.assertEqual(temperature, 22.5)
        self.assertEqual(call_count, 2)
    
    def test_store_temperature_success(self):
        """Test successful temperature storage."""
        success = self.daemon.store_temperature(
            'living_room_thermometer', 22.5, 65.0
        )
        
        self.assertTrue(success)
        
        # Verify record was created
        temp_record = Temperature.objects.filter(location='Living Room').first()
        self.assertIsNotNone(temp_record)
        self.assertEqual(temp_record.temperature, 22.5)
        self.assertEqual(temp_record.humidity, 65.0)
    
    def test_store_temperature_invalid_type(self):
        """Test temperature storage with invalid data types."""
        success = self.daemon.store_temperature(
            'living_room_thermometer', 'invalid', 65.0
        )
        
        self.assertFalse(success)
        self.assertEqual(Temperature.objects.count(), 0)
    
    def test_store_temperature_unknown_device(self):
        """Test temperature storage for unknown device."""
        success = self.daemon.store_temperature(
            'unknown_device', 22.5, 65.0
        )
        
        # Should still succeed but log warning
        self.assertTrue(success)
        
        temp_record = Temperature.objects.first()
        self.assertEqual(temp_record.location, 'Unknown')


class TemperatureDaemonMainLoopTests(TemperatureDaemonTestCase):
    """Test daemon main loop functionality."""
    
    @patch('scripts.temperature_daemon.SwitchBot')
    @patch('time.sleep')
    def test_daemon_run_single_cycle(self, mock_sleep, mock_switchbot_class):
        """Test daemon running a single cycle."""
        from scripts.temperature_daemon import TemperatureDaemon
        
        # Mock SwitchBot
        mock_switchbot = MockSwitchBot()
        mock_switchbot_class.return_value = mock_switchbot
        
        # Add mock devices
        for mac in ['MAC001', 'MAC002', 'MAC003', 'MAC004']:
            device = MockSwitchBotDevice(
                temperature='20.0', 
                humidity='50', 
                device_id=mac
            )
            mock_switchbot.add_device(mac, device)
        
        daemon = TemperatureDaemon()
        
        # Stop daemon after first cycle
        original_sleep = daemon.interval
        daemon.interval = 0.1
        
        def stop_daemon(*args):
            daemon.running = False
        
        mock_sleep.side_effect = stop_daemon
        
        # Run daemon
        daemon.run()
        
        # Verify data was collected
        self.assertEqual(Temperature.objects.count(), 4)
        
        # Verify all locations are present
        locations = set(Temperature.objects.values_list('location', flat=True))
        expected_locations = {'Living Room', 'Bedroom', 'Office', 'Outdoor'}
        self.assertEqual(locations, expected_locations)
    
    @patch('scripts.temperature_daemon.SwitchBot')
    @patch('time.sleep')
    def test_daemon_run_consecutive_failures(self, mock_sleep, mock_switchbot_class):
        """Test daemon handling of consecutive failures."""
        from scripts.temperature_daemon import TemperatureDaemon
        
        # Mock SwitchBot with failing devices
        mock_switchbot = MockSwitchBot()
        mock_switchbot_class.return_value = mock_switchbot
        
        # All devices fail
        for mac in ['MAC001', 'MAC002', 'MAC003', 'MAC004']:
            device = MockSwitchBotDevice(device_id=mac)
            device.set_failure(True, "Device communication error")
            mock_switchbot.add_device(mac, device)
        
        daemon = TemperatureDaemon()
        daemon.interval = 0.1
        
        # Mock sleep to count cycles
        cycle_count = 0
        def count_cycles(*args):
            nonlocal cycle_count
            cycle_count += 1
            if cycle_count >= 6:  # Stop after max failures
                daemon.running = False
        
        mock_sleep.side_effect = count_cycles
        
        # Run daemon - should stop after max consecutive failures
        daemon.run()
        
        # Should have stopped due to consecutive failures
        self.assertEqual(Temperature.objects.count(), 0)
        self.assertGreaterEqual(cycle_count, 4)  # At least 4 cycles before stopping
    
    @patch('scripts.temperature_daemon.SwitchBot')
    def test_daemon_signal_handling(self, mock_switchbot_class):
        """Test daemon signal handling for graceful shutdown."""
        from scripts.temperature_daemon import TemperatureDaemon
        import signal
        
        # Mock SwitchBot
        mock_switchbot = MockSwitchBot()
        mock_switchbot_class.return_value = mock_switchbot
        
        daemon = TemperatureDaemon()
        
        # Verify daemon is running
        self.assertTrue(daemon.running)
        
        # Send SIGINT signal
        daemon._signal_handler(signal.SIGINT, None)
        
        # Verify daemon is stopped
        self.assertFalse(daemon.running)