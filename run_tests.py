#!/usr/bin/env python
"""
Test runner script for the temperature monitoring project.
"""

import os
import sys
import django
from django.test.utils import get_runner
from django.conf import settings


def run_tests():
    """Run all tests for the project."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'temperature.test_settings')
    django.setup()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True)
    
    # Run all tests
    failures = test_runner.run_tests(['homepage'])
    
    if failures:
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")


def run_specific_tests(test_names):
    """Run specific tests."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'temperature.test_settings')
    django.setup()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True)
    
    failures = test_runner.run_tests(test_names)
    
    if failures:
        sys.exit(1)
    else:
        print(f"\n✅ Tests {test_names} passed!")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Run specific tests
        test_names = sys.argv[1:]
        run_specific_tests(test_names)
    else:
        # Run all tests
        run_tests()