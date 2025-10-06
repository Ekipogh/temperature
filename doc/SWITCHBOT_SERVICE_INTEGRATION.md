# SwitchBot Service Integration

This document describes the shared SwitchBot service that is now available for both the temperature daemon and the Django web application.

## Architecture Overview

The SwitchBot functionality has been refactored into a shared service module located at `services/switchbot_service.py`. This provides:

1. **Consistent API**: Both the daemon and web application use the same interface
2. **Environment-based Configuration**: Automatic switching between production and pre-production modes
3. **Centralized Device Management**: Single source of truth for device configurations
4. **Better Testing**: Pre-production service provides realistic mock data

## Service Components

### SwitchBotService (Base Class)
- Handles real SwitchBot API communication
- Provides methods for temperature, humidity, and full device status
- Manages authentication and error handling

### PreProdSwitchBotService (Test Class)
- Extends the base service for testing/development
- Returns realistic random data instead of calling real APIs
- Useful for development and CI/CD environments

### Factory Function
```python
from services.switchbot_service import get_switchbot_service

# Automatically returns the correct service based on ENVIRONMENT variable
service = get_switchbot_service()
```

## Environment Configuration

The service automatically selects the appropriate implementation based on the `ENVIRONMENT` environment variable:

- `ENVIRONMENT=production` → Uses real SwitchBot API
- `ENVIRONMENT=preprod` → Uses mock data service

## Device Configuration

Centralized device configuration is available through helper functions:

```python
from services.switchbot_service import get_device_configs, get_location_mac_mapping

# Get device configs with technical names
configs = get_device_configs()
# Returns: {"living_room_thermometer": "MAC1", "bedroom_thermometer": "MAC2", ...}

# Get human-readable location mapping
locations = get_location_mac_mapping()
# Returns: {"Living Room": "MAC1", "Bedroom": "MAC2", ...}
```

## Usage in Daemon

The temperature daemon (`scripts/temperature_daemon.py`) now uses the shared service:

```python
from services.switchbot_service import get_switchbot_service, get_device_configs

class TemperatureDaemon:
    def __init__(self):
        # Automatically gets the right service (production vs preprod)
        self.switchbot_service = get_switchbot_service()
        self.devices = get_device_configs()
```

## Usage in Django Views

The Django views (`homepage/views.py`) have been updated to use the shared service:

```python
from services.switchbot_service import get_switchbot_service, get_location_mac_mapping

def fetch_new_data():
    switchbot_service = get_switchbot_service()
    devices = get_location_mac_mapping()

    for location, mac in devices.items():
        status = switchbot_service.get_device_status(mac)
        # Process and save data...
```

## Benefits

1. **Code Reuse**: No duplicate SwitchBot logic between daemon and web app
2. **Consistency**: Same data processing logic everywhere
3. **Testing**: Easy to test with mock data in preprod environment
4. **Maintenance**: Single place to update SwitchBot integration
5. **Environment Flexibility**: Seamless switching between production and test modes

## Docker Integration

The services module is automatically available in both Docker containers:

- **temperature-daemon container**: Uses the service for periodic data collection
- **django-app container**: Uses the service for manual data refresh and status checks

Both containers receive the same environment variables and will use the appropriate service implementation based on the `ENVIRONMENT` setting.

## Pre-Production Testing

When `ENVIRONMENT=preprod`, the system will:

1. Use `PreProdSwitchBotService` instead of real API calls
2. Generate realistic random temperature data (18-25°C)
3. Generate realistic random humidity data (30-50%)
4. Include mock battery status in device status
5. Log that it's running in pre-production mode

This allows for complete end-to-end testing without consuming SwitchBot API quotas or requiring real devices.