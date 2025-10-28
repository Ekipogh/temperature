import json
import os
import csv
import subprocess
import sys
import django
import logging
import re
from django.utils import timezone
from datetime import datetime, timezone as dt_timezone
from pathlib import Path

# Adjust the Python path to include the project directory
project_dir = Path(__file__).parent.parent  # Point to project root
sys.path.append(str(project_dir))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(
        "govee_service.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class DjangoDatabaseService:
    def __init__(self):
        # Setup Django
        database_path = os.getenv("GOVEE_DJANGO_DB_PATH", os.path.join(
            project_dir, "data", "db.sqlite3"))
        os.environ["DATABASE_PATH"] = database_path
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "temperature.settings")
        django.setup()

    def convert_timestamp(self, timestamp_str: str) -> timezone.datetime:
        # Parse the timestamp string from the device
        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

        # FIXED: Properly handle timezone conversion with DST awareness
        # The Govee device outputs timestamps in local system time
        # We need to convert them to UTC for database storage

        import zoneinfo
        from datetime import timedelta

        # Get the system's local timezone (handles DST automatically)
        # This will be "Europe/London" or similar, which knows about GMT/BST transitions
        try:
            # Try to get the system timezone
            local_tz = datetime.now().astimezone().tzinfo

            # Make the naive datetime timezone-aware in local timezone
            dt_local = dt.replace(tzinfo=local_tz)

            # Convert to UTC
            dt_utc = dt_local.astimezone(dt_timezone.utc)

        except Exception:
            # Fallback: if we can't determine system timezone properly,
            # use zoneinfo for Europe/London (GMT/BST)
            try:
                london_tz = zoneinfo.ZoneInfo("Europe/London")
                dt_local = dt.replace(tzinfo=london_tz)
                dt_utc = dt_local.astimezone(dt_timezone.utc)
            except Exception:
                # Final fallback: manual DST detection
                import time
                is_dst = time.daylight and time.localtime().tm_isdst
                offset_hours = 1 if is_dst else 0
                dt_utc_naive = dt - timedelta(hours=offset_hours)
                dt_utc = dt_utc_naive.replace(tzinfo=dt_timezone.utc)

        return dt_utc

    def save_temperature_humidity(self, timestamp_str: str, location: str, temperature: float, humidity: float):
        timestamp = self.convert_timestamp(timestamp_str)

        from homepage.models import Temperature
        temp_record = Temperature(
            timestamp=timestamp,
            location=location,
            temperature=temperature,
            humidity=humidity
        )
        temp_record.save()


class GoveeService:
    def __init__(self):
        # Initialize Django database service
        self.db_service = DjangoDatabaseService()
        # govee-h5075 executable path
        _exe_path = os.path.join("thirdparty", "govee", "govee-h5075.py")

        self.interval = 300  # Default interval in seconds
        interval_env = os.getenv("GOVEE_POLL_INTERVAL")
        if interval_env:
            try:
                self.interval = int(interval_env)
            except ValueError:
                logging.error(
                    f"Invalid interval value: {interval_env}. Using default: {self.interval} seconds.")

        # Use the current Python executable (from the active virtual environment)
        python_executable = sys.executable

        self._command = [python_executable, _exe_path,
                         "-m", "--interval", str(self.interval)]
        self._env = os.environ.copy()
        self._env["PYTHONUNBUFFERED"] = "1"  # Ensure unbuffered output

        self.status = {
            "status": "initialized",
            "last_update": None,
            "error": None,
        }
        self.status_file_path = os.getenv(
            "GOVEE_STATUS_FILE", "govee_status.json")
        self.pid_file_path = os.getenv("GOVEE_PID_FILE", "govee_service.pid")
        self.update_status("initialized")
        with open(self.pid_file_path, "w") as f:
            f.write(str(os.getpid()))


    def run_subprocess(self, command, env=None, callback=None):
        """Run a subprocess command and optionally process its output with a callback."""
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
            encoding="utf-8",
            errors="replace"  # Replace invalid UTF-8 bytes instead of failing
        )

        if not process.stdout:
            logger.error("Failed to capture subprocess output.")
            return
        with process.stdout:
            for line in iter(process.stdout.readline, ""):
                line = line.strip()  # Remove whitespace and newlines
                if line:  # Only process non-empty lines
                    if callback:
                        callback(line)
                        self.status["last_update"] = timezone.now().isoformat()
                        self.update_status("running")
        process.wait()

    def handle_output(self, line):
        """Handle output lines from the subprocess."""
        # Skip header lines and empty lines
        if not line or "MAC-Address/Alias" in line or "Starting continuous" in line or "Press Ctrl+C" in line or len(line) == 0:
            return

        # Avoid duplicate processing
        if hasattr(self, '_last_line') and self._last_line == line:
            return
        self._last_line = line

        # Process the line
        # Timestamp             MAC-Address/Alias     Device name   Temperature  Dew point  Temperature  Dew point  Rel. humidity  Abs. humidity  Steam pressure  Battery
        # 2025-10-13 06:08:47   Landing               GVH5075_496E  20.2°C       11.1°C     68.4°F       52.0°F     55.8%          9.8 g/m³      13.2 mbar       34%
        parts = list(csv.reader([line], delimiter=' ',
                     skipinitialspace=True))[0]
        if len(parts) < 11:
            logger.error(f"Unexpected line format: {line}")
            return
        timestamp = f"{parts[0]} {parts[1]}"
        alias = parts[2]
        device_name = parts[3]
        store_name = device_name if ":" in alias else alias
        temperature = float(parts[4].replace("°C", "").strip())
        humidity = float(parts[8].replace("%", "").strip())
        # Process the extracted values as needed

        logger.info(
            f"Saving data - Timestamp: {timestamp}, Alias: {store_name}, Temperature: {temperature}°C, Humidity: {humidity}%")
        # Save the data to the database
        self.db_service.save_temperature_humidity(
            timestamp, store_name, temperature, humidity)

    def update_status(self, status: str):
        self.status["status"] = status
        with open(self.status_file_path, "w", encoding="utf-8") as f:
            json.dump(self.status, f, ensure_ascii=False)

    def run(self):
        logger.info("Starting Govee Service...")
        # Run the govee-h5075 script in background
        try:
            self.run_subprocess(self._command, env=self._env,
                                callback=self.handle_output)
        except Exception as e:
            logger.error(f"Error occurred while running Govee Service: {e}")
        logger.info("Govee Service stopped.")
        self.update_status("stopped")


if __name__ == "__main__":
    GoveeService().run()
