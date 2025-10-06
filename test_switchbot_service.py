#!/usr/bin/env python3
"""
Test script for the shared SwitchBot service.
This script can be used to verify that both production and pre-production services work correctly.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Set test environment variables
os.environ.setdefault("SWITCHBOT_TOKEN", "test_token")
os.environ.setdefault("SWITCHBOT_SECRET", "test_secret")
os.environ.setdefault("LIVING_ROOM_MAC", "TEST_MAC_001")
os.environ.setdefault("BEDROOM_MAC", "TEST_MAC_002")
os.environ.setdefault("OFFICE_MAC", "TEST_MAC_003")
os.environ.setdefault("OUTDOOR_MAC", "TEST_MAC_004")

from services.switchbot_service import (
    get_switchbot_service,
    get_device_configs,
    get_location_mac_mapping,
    SwitchBotService,
    PreProdSwitchBotService
)


def test_service_factory():
    """Test the service factory function."""
    print("Testing SwitchBot service factory...")

    # Test production mode
    os.environ["ENVIRONMENT"] = "production"
    service = get_switchbot_service()
    print(f"Production service type: {type(service).__name__}")
    assert isinstance(service, SwitchBotService)
    assert not isinstance(service, PreProdSwitchBotService)

    # Test pre-production mode
    os.environ["ENVIRONMENT"] = "preprod"
    service = get_switchbot_service()
    print(f"Pre-production service type: {type(service).__name__}")
    assert isinstance(service, PreProdSwitchBotService)

    print("✅ Service factory tests passed!")


def test_device_configs():
    """Test device configuration functions."""
    print("\nTesting device configuration...")

    # Test device configs
    configs = get_device_configs()
    print(f"Device configs: {configs}")
    assert "living_room_thermometer" in configs
    assert "bedroom_thermometer" in configs
    assert "office_thermometer" in configs
    assert "outdoor_thermometer" in configs

    # Test location mapping
    mapping = get_location_mac_mapping()
    print(f"Location mapping: {mapping}")
    assert "Living Room" in mapping
    assert "Bedroom" in mapping
    assert "Office" in mapping
    assert "Outdoor" in mapping

    print("✅ Device configuration tests passed!")


def test_preprod_service():
    """Test the pre-production service functionality."""
    print("\nTesting pre-production service...")

    service = PreProdSwitchBotService()
    test_mac = "TEST_MAC_001"

    # Test temperature
    temp = service.get_temperature(test_mac)
    print(f"Pre-prod temperature: {temp}°C")
    assert temp is not None
    assert 18.0 <= temp <= 25.0

    # Test humidity
    humidity = service.get_humidity(test_mac)
    print(f"Pre-prod humidity: {humidity}%")
    assert humidity is not None
    assert 30.0 <= humidity <= 50.0

    # Test device status
    status = service.get_device_status(test_mac)
    print(f"Pre-prod device status: {status}")
    assert status is not None
    assert "temperature" in status
    assert "humidity" in status
    assert "battery" in status

    print("✅ Pre-production service tests passed!")


def main():
    """Run all tests."""
    print("🧪 Testing shared SwitchBot service implementation...")
    print("=" * 60)

    try:
        test_service_factory()
        test_device_configs()
        test_preprod_service()

        print("\n" + "=" * 60)
        print("🎉 All tests passed! The shared SwitchBot service is working correctly.")
        print("\n📋 Summary:")
        print("✅ Service factory creates correct service types based on ENVIRONMENT")
        print("✅ Device configuration functions work correctly")
        print("✅ Pre-production service generates realistic test data")
        print("\n🚀 Ready for deployment!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()