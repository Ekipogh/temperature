"""
Management command to check daemon status.
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from homepage.views import get_daemon_status


class Command(BaseCommand):
    help = "Check the status of the temperature daemon"

    def add_arguments(self, parser):
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output status as JSON",
        )
        parser.add_argument(
            "--detailed",
            action="store_true",
            help="Show detailed status information",
        )

    def handle(self, *args, **options):
        status = get_daemon_status()

        if options["json"]:
            self.stdout.write(json.dumps(status, indent=2))
            return

        # Human-readable output
        self.stdout.write("Temperature Daemon Status")
        self.stdout.write("=" * 25)

        running = status.get("running", False)
        daemon_status = status.get("status", "unknown")

        if running and daemon_status == "active":
            self.stdout.write(self.style.SUCCESS(f"Status: {daemon_status.upper()}"))
        elif daemon_status == "stale":
            self.stdout.write(self.style.WARNING(f"Status: {daemon_status.upper()}"))
        else:
            self.stdout.write(self.style.ERROR(f"Status: {daemon_status.upper()}"))

        if "error" in status:
            self.stdout.write(self.style.ERROR(f"Error: {status['error']}"))

        if options["detailed"] or not running:
            self.stdout.write(f"Running: {running}")

            if "started_at" in status:
                self.stdout.write(f"Started: {status['started_at']}")

            if "last_update" in status:
                self.stdout.write(f"Last Update: {status['last_update']}")

            if "uptime_seconds" in status:
                uptime = status["uptime_seconds"]
                hours = uptime // 3600
                minutes = (uptime % 3600) // 60
                self.stdout.write(f"Uptime: {hours}h {minutes}m")

            if "iteration_count" in status:
                self.stdout.write(f"Iterations: {status['iteration_count']}")

            if "consecutive_failures" in status:
                failures = status["consecutive_failures"]
                if failures > 0:
                    self.stdout.write(
                        self.style.WARNING(f"Consecutive Failures: {failures}")
                    )
                else:
                    self.stdout.write(f"Consecutive Failures: {failures}")

            if "devices" in status:
                self.stdout.write(f"Devices: {', '.join(status['devices'])}")

            if (
                "last_successful_reading" in status
                and status["last_successful_reading"]
            ):
                self.stdout.write(
                    f"Last Successful Reading: {status['last_successful_reading']}"
                )
