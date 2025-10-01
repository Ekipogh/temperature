#!/usr/bin/env python
"""
Comprehensive test runner for the temperature monitoring project.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n🔍 {description}")
    print("=" * 50)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=False)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED (exit code: {e.returncode})")
        return False


def main():
    """Run all tests and checks."""
    print("🧪 Temperature Monitor - Comprehensive Test Suite")
    print("=" * 60)
    
    # Ensure we're in the project directory
    os.chdir(Path(__file__).parent)
    
    # Set test environment
    os.environ['DJANGO_SETTINGS_MODULE'] = 'temperature.test_settings'
    
    # Create test environment file
    test_env_content = """
SWITCHBOT_TOKEN=test_token_for_testing
SWITCHBOT_SECRET=test_secret_for_testing
LIVING_ROOM_MAC=TEST_MAC_001
BEDROOM_MAC=TEST_MAC_002
OFFICE_MAC=TEST_MAC_003
OUTDOOR_MAC=TEST_MAC_004
TEMPERATURE_INTERVAL=60
"""
    
    with open('.env.test', 'w') as f:
        f.write(test_env_content.strip())
    
    # Test commands
    test_commands = [
        (
            "python manage.py check --settings=temperature.test_settings",
            "Django System Checks"
        ),
        (
            "python manage.py makemigrations --check --dry-run --settings=temperature.test_settings",
            "Migration Consistency Check"
        ),
        (
            "python manage.py test --settings=temperature.test_settings --verbosity=2",
            "Django Unit Tests"
        ),
        (
            "python -m pytest --tb=short --disable-warnings",
            "Pytest Test Runner"
        ),
    ]
    
    # Code quality checks (if tools are available)
    quality_commands = [
        (
            "python -m flake8 homepage/ scripts/ temperature/ --max-line-length=88 --exclude=migrations",
            "Code Style Check (flake8)"
        ),
        (
            "python -m black --check homepage/ scripts/ temperature/",
            "Code Formatting Check (black)"
        ),
        (
            "python -m isort --check-only homepage/ scripts/ temperature/",
            "Import Sorting Check (isort)"
        ),
    ]
    
    # Security checks
    security_commands = [
        (
            "python -m safety check --json",
            "Security Vulnerability Check (safety)"
        ),
        (
            "python -m bandit -r homepage/ scripts/ temperature/ -f json",
            "Security Code Analysis (bandit)"
        ),
    ]
    
    results = []
    
    # Run core tests
    print("\n📋 Running Core Tests")
    for command, description in test_commands:
        success = run_command(command, description)
        results.append((description, success))
    
    # Run code quality checks (optional)
    print("\n🎨 Running Code Quality Checks")
    for command, description in quality_commands:
        try:
            success = run_command(command, description)
            results.append((description, success))
        except Exception:
            print(f"⚠️  {description} - SKIPPED (tool not installed)")
            results.append((description, None))
    
    # Run security checks (optional)
    print("\n🔒 Running Security Checks")
    for command, description in security_commands:
        try:
            success = run_command(command, description)
            results.append((description, success))
        except Exception:
            print(f"⚠️  {description} - SKIPPED (tool not installed)")
            results.append((description, None))
    
    # Generate coverage report if pytest-cov is available
    try:
        print(f"\n📊 Generating Coverage Report")
        run_command(
            "python -m pytest --cov=homepage --cov=scripts --cov-report=html --cov-report=term-missing",
            "Coverage Report Generation"
        )
        print("📄 Coverage report generated: htmlcov/index.html")
    except Exception:
        print("⚠️  Coverage report - SKIPPED (pytest-cov not installed)")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success is True)
    failed = sum(1 for _, success in results if success is False)
    skipped = sum(1 for _, success in results if success is None)
    
    for description, success in results:
        if success is True:
            status = "✅ PASSED"
        elif success is False:
            status = "❌ FAILED"
        else:
            status = "⚠️  SKIPPED"
        
        print(f"{status:12} {description}")
    
    print("\n" + "=" * 60)
    print(f"📈 Results: {passed} passed, {failed} failed, {skipped} skipped")
    
    # Clean up
    try:
        os.remove('.env.test')
    except FileNotFoundError:
        pass
    
    if failed > 0:
        print("\n❌ Some tests failed. Please check the output above.")
        sys.exit(1)
    else:
        print("\n🎉 All tests passed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()