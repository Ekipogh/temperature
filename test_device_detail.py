"""
Test file for device detail functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'temperature.settings')
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from homepage.models import Temperature
from django.utils import timezone
from datetime import timedelta


class DeviceDetailTests(TestCase):
    def setUp(self):
        """Create test data for device detail tests."""
        self.client = Client()

        # Create test temperature data
        base_time = timezone.now()
        for i in range(10):
            Temperature.objects.create(
                location='Living Room',
                temperature=20.0 + i,
                humidity=50.0 + i,
                timestamp=base_time - timedelta(hours=i)
            )

    def test_device_detail_view_loads(self):
        """Test that device detail view loads successfully."""
        response = self.client.get('/device/living-room/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Living Room Device Dashboard')
        self.assertContains(response, 'Temperature')
        self.assertContains(response, 'Humidity')

    def test_device_detail_with_statistics(self):
        """Test that device detail shows statistics."""
        response = self.client.get('/device/living-room/')
        self.assertEqual(response.status_code, 200)

        # Check that context contains expected data
        self.assertIn('latest_reading', response.context)
        self.assertIn('hourly_avg', response.context)
        self.assertIn('daily_avg', response.context)
        self.assertIn('total_stats', response.context)

    def test_device_detail_nonexistent_location(self):
        """Test 404 for non-existent location."""
        response = self.client.get('/device/nonexistent/')
        self.assertEqual(response.status_code, 404)

    def test_device_detail_url_patterns(self):
        """Test various device URL patterns work."""
        test_cases = [
            ('living-room', 'Living Room'),
            ('bedroom', 'Bedroom'),
            ('office', 'Office'),
            ('outdoor', 'Outdoor')
        ]

        for device_name, location in test_cases:
            # Create some data for this location
            Temperature.objects.create(
                location=location,
                temperature=20.0,
                humidity=50.0,
                timestamp=timezone.now()
            )

            response = self.client.get(f'/device/{device_name}/')
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, location)


if __name__ == '__main__':
    import unittest
    unittest.main()
