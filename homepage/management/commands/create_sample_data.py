from django.core.management.base import BaseCommand
from django.utils import timezone
from homepage.models import Temperature
import random
from datetime import timedelta


class Command(BaseCommand):
    help = 'Create sample temperature data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days of sample data to create (default: 7)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new sample data'
        )

    def handle(self, *args, **options):
        if options['clear']:
            Temperature.objects.all().delete()
            self.stdout.write(
                self.style.WARNING('Cleared all existing temperature data')
            )

        days = options['days']
        locations = ['Living Room', 'Bedroom', 'Office', 'Outdoor']

        # Temperature ranges for different locations
        temp_ranges = {
            'Living Room': (20, 25),
            'Bedroom': (18, 23),
            'Office': (21, 26),
            'Outdoor': (-5, 35)
        }

        # Humidity ranges
        humidity_ranges = {
            'Living Room': (40, 60),
            'Bedroom': (45, 65),
            'Office': (35, 55),
            'Outdoor': (30, 90)
        }

        created_count = 0
        start_time = timezone.now() - timedelta(days=days)

        for day in range(days):
            for hour in range(0, 24, 2):  # Every 2 hours
                for location in locations:
                    timestamp = start_time + timedelta(days=day, hours=hour)

                    # Generate realistic temperature
                    min_temp, max_temp = temp_ranges[location]
                    temperature = round(random.uniform(min_temp, max_temp), 1)

                    # Generate realistic humidity
                    min_hum, max_hum = humidity_ranges[location]
                    humidity = round(random.uniform(min_hum, max_hum), 1)

                    # Add some seasonal variation for outdoor temps
                    if location == 'Outdoor':
                        # Simulate day/night temperature variation
                        if 6 <= hour <= 18:  # Daytime
                            temperature += random.uniform(2, 5)
                        else:  # Nighttime
                            temperature -= random.uniform(1, 3)
                        temperature = round(temperature, 1)

                    Temperature.objects.create(
                        location=location,
                        temperature=temperature,
                        humidity=humidity,
                        timestamp=timestamp
                    )
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} temperature records '
                f'for {days} days'
            )
        )