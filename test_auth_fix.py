#!/usr/bin/env python3
"""
Test script to verify the SwitchBot authentication fix.
This script simulates the 401 error scenario to test the retry mechanism.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "temperature.settings")
django.setup()

from services.switchbot_service import get_switchbot_service

def test_authentication_recovery():
    """Test that the service properly handles authentication errors."""
    print("Testing SwitchBot authentication recovery...")

    service = get_switchbot_service()

    # Test with your actual device MAC
    test_mac = os.getenv("LIVING_ROOM_MAC", "D40E84863006")

    print(f"Testing with device MAC: {test_mac}")

    # Make several requests to trigger the 401 error
    for i in range(10):
        print(f"\n--- Request {i+1}/10 ---")

        temp = service.get_temperature(test_mac)
        humidity = service.get_humidity(test_mac)

        if temp is not None:
            print(f"✅ Temperature: {temp}°C")
        else:
            print(f"❌ Temperature: Failed")

        if humidity is not None:
            print(f"✅ Humidity: {humidity}%")
        else:
            print(f"❌ Humidity: Failed")

        # If both failed, the authentication issue might be occurring
        if temp is None and humidity is None:
            print("⚠️  Both readings failed - possible auth issue")

        # Small delay between requests
        import time
        time.sleep(2)

    print("\n" + "="*50)
    print("Test completed!")
    print("If requests succeed throughout, the fix is working.")
    print("Previous behavior: Requests 7+ would fail with 401 errors.")

if __name__ == "__main__":
    test_authentication_recovery()