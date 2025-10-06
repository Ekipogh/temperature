# Test Updates for SwitchBotService Architecture

## Problem Summary

The tests were failing in the "preprod" environment because:

1. The temperature daemon now uses a new `SwitchBotService` architecture
2. In "preprod" environment, it uses `PreProdSwitchBotService` which returns random values (18-25°C temp, 30-50% humidity)
3. The old tests expected `None` values but were receiving random values instead
4. Tests were still mocking the old direct `SwitchBot` class instead of the new service layer

## Changes Made

### 1. Updated Test Utilities (`test_utils.py`)

**Added new mock service classes:**
- `MockSwitchBotService`: Base mock service for testing
- `MockTestSwitchBotService`: Service that returns `None` (for testing failure scenarios)

**Features:**
- Configurable temperature/humidity values per device
- Failure simulation capabilities
- Clean interface matching the real service classes

### 2. Updated Daemon Tests (`test_daemon.py`)

**Key Changes:**
- Tests now use service architecture instead of direct SwitchBot mocking
- Added environment-specific initialization tests
- Tests for both production and preprod environments
- Updated to work with MAC address-based device storage
- Added specific tests for `PreProdSwitchBotService` behavior

**New Test Methods:**
- `test_daemon_initialization_success_production()`
- `test_daemon_initialization_success_preprod()`
- `test_daemon_environment_service_selection()`
- `test_preprod_service_returns_random_values()`

### 3. Updated View Tests (`tests.py`)

**Key Changes:**
- Added `ENVIRONMENT=test` to test environment variables
- Added preprod environment behavior testing
- Added null safety checks for database queries
- Maintains backward compatibility with existing API tests

**New Test Methods:**
- `test_fetch_new_data_preprod_environment()`

### 4. Environment-Based Testing

**Test Environment Modes:**
- `ENVIRONMENT=test`: Uses regular service with proper mocking (returns `None` when expected)
- `ENVIRONMENT=preprod`: Uses `PreProdSwitchBotService` (returns random values)
- `ENVIRONMENT=production`: Uses real `SwitchBotService` (requires valid credentials)

## How Tests Now Work

### Production Environment Tests
```python
with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
    # Uses SwitchBotService with mocking
    daemon = TemperatureDaemon()
```

### Preprod Environment Tests
```python
with patch.dict(os.environ, {"ENVIRONMENT": "preprod"}):
    # Uses PreProdSwitchBotService (returns random data)
    daemon = TemperatureDaemon()
```

### Test Environment
```python
with patch.dict(os.environ, {"ENVIRONMENT": "test"}):
    # Uses MockSwitchBotService (controllable behavior)
    daemon = TemperatureDaemon()
```

## Running Tests

### Run All Tests
```bash
python manage.py test
```

### Run Specific Test Categories
```bash
# Model tests
python manage.py test homepage.tests.TemperatureModelTests

# View tests
python manage.py test homepage.tests.TemperatureViewTests

# Daemon tests
python manage.py test homepage.test_daemon

# API tests
python manage.py test homepage.tests.FetchNewDataTests
```

### Test Environment Behavior
```bash
python test_environment.py
```

## Key Features

### 1. Environment Isolation
- Tests are isolated from production/preprod behavior
- Each environment uses appropriate service implementation
- No cross-contamination between test modes

### 2. Proper Mocking
- Services are mocked at the correct abstraction level
- Mock services provide controllable, predictable behavior
- Failure scenarios can be simulated reliably

### 3. Null Safety
- All database queries include null checks
- Tests handle missing data gracefully
- Type safety maintained throughout

### 4. Backward Compatibility
- Existing API tests continue to work
- View functionality tests remain intact
- Model validation tests unchanged

## Troubleshooting

### If Tests Still Fail in Preprod

1. **Check Environment Variable:**
   ```python
   import os
   print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'not set')}")
   ```

2. **Verify Service Selection:**
   ```python
   from scripts.temperature_daemon import TemperatureDaemon
   daemon = TemperatureDaemon()
   print(f"Service type: {type(daemon.switchbot_service)}")
   ```

3. **Test Service Directly:**
   ```python
   from scripts.temperature_daemon import PreProdSwitchBotService
   service = PreProdSwitchBotService()
   temp = service.get_temperature("test")
   print(f"Temperature: {temp}")  # Should be 18-25°C
   ```

### Expected Behaviors by Environment

| Environment | Service Used | Temperature Returns | Humidity Returns |
|-------------|--------------|-------------------|------------------|
| `test` | MockSwitchBotService | Configurable/None | Configurable/None |
| `preprod` | PreProdSwitchBotService | 18.0-25.0°C | 30.0-50.0% |
| `production` | SwitchBotService | Real API data | Real API data |

## Summary

The tests are now properly updated to work with the new `SwitchBotService` architecture. They correctly handle the environment-based service selection and provide appropriate mocking for each environment type. The preprod environment behavior (returning random values) is now properly tested and isolated from other test scenarios.