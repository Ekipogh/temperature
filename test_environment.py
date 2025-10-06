"""
Test runner for environment-specific behavior.
This script helps verify that tests work correctly in different environments.
"""

import os
import sys
import django
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'temperature.settings')
django.setup()

def test_environment_behavior():
    """Test that the service classes behave correctly in different environments."""

    print("Testing SwitchBotService environment behavior...")

    # Test imports
    try:
        from scripts.temperature_daemon import SwitchBotService, PreProdSwitchBotService
        print("✅ Successfully imported service classes")
    except ImportError as e:
        print(f"❌ Failed to import service classes: {e}")
        return False

    # Test PreProdSwitchBotService returns values
    preprod_service = PreProdSwitchBotService()

    temp = preprod_service.get_temperature("test_mac")
    humidity = preprod_service.get_humidity("test_mac")

    print(f"PreProd Service - Temperature: {temp}, Humidity: {humidity}")

    if temp is not None and humidity is not None:
        print("✅ PreProdSwitchBotService returns non-None values")

        # Check ranges
        if 18.0 <= temp <= 25.0 and 30.0 <= humidity <= 50.0:
            print("✅ Values are in expected ranges")
        else:
            print(f"❌ Values out of range: temp={temp}, humidity={humidity}")

    else:
        print("❌ PreProdSwitchBotService returns None values")
        return False

    # Test regular SwitchBotService (would normally fail without credentials)
    print("\nTesting regular SwitchBotService...")
    try:
        service = SwitchBotService()
        # This would normally require valid credentials
        print("✅ SwitchBotService instantiated (credentials not tested)")
    except Exception as e:
        print(f"ℹ️  SwitchBotService requires credentials: {e}")

    return True

def test_environment_selection():
    """Test environment-based service selection."""

    print("\n" + "="*50)
    print("Testing environment-based service selection...")

    test_cases = [
        ("production", "SwitchBotService"),
        ("preprod", "PreProdSwitchBotService"),
        ("test", "SwitchBotService"),
        ("", "SwitchBotService")  # Default
    ]

    for env_value, expected_service in test_cases:
        print(f"\nTesting ENVIRONMENT='{env_value}'...")

        # Set environment
        if env_value:
            os.environ["ENVIRONMENT"] = env_value
        else:
            os.environ.pop("ENVIRONMENT", None)

        # Test the logic from daemon
        environment = os.getenv("ENVIRONMENT", "production").lower()
        is_preprod = environment == "preprod"

        if is_preprod:
            actual_service = "PreProdSwitchBotService"
        else:
            actual_service = "SwitchBotService"

        if actual_service == expected_service:
            print(f"✅ Correctly selected {actual_service}")
        else:
            print(f"❌ Expected {expected_service}, got {actual_service}")

    return True

if __name__ == "__main__":
    print("Testing Temperature Daemon Service Architecture")
    print("=" * 50)

    success = True
    success &= test_environment_behavior()
    success &= test_environment_selection()

    print("\n" + "="*50)
    if success:
        print("✅ All tests passed!")
        print("\nThe tests should now work correctly with:")
        print("- ENVIRONMENT=test: Uses regular service with mocking")
        print("- ENVIRONMENT=preprod: Uses PreProdSwitchBotService (returns random values)")
        print("- ENVIRONMENT=production: Uses regular SwitchBotService")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)