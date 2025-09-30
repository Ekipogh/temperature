from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from homepage.models import Temperature


class Command(BaseCommand):
    help = 'Debug temperature data'

    def handle(self, *args, **options):
        total = Temperature.objects.count()
        self.stdout.write(f"Total records: {total}")

        if total == 0:
            self.stdout.write("No temperature records found!")
            return

        # Check records in last 24 hours
        recent = Temperature.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=24)
        )

        self.stdout.write(f"Records in last 24h: {recent.count()}")

        if recent.exists():
            latest = recent.latest('timestamp')
            earliest = recent.earliest('timestamp')
            self.stdout.write(f"Latest: {latest.timestamp} - {latest.location}: {latest.temperature}°C")
            self.stdout.write(f"Earliest: {earliest.timestamp} - {earliest.location}: {earliest.temperature}°C")
        else:
            # Check what timestamps we actually have
            all_temps = Temperature.objects.order_by('-timestamp')[:5]
            self.stdout.write("Most recent records:")
            for temp in all_temps:
                self.stdout.write(f"  {temp.timestamp} - {temp.location}: {temp.temperature}°C")