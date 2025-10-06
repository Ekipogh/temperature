import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from switchbot import SwitchBot

from django.db import models
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from homepage.models import Temperature


def get_daemon_status():
    """Get the current status of the temperature daemon."""
    status_file = Path(os.getenv("DAEMON_STATUS_FILE", Path(__file__).parent.parent / "daemon_status.json"))

    default_status = {
        "running": False,
        "status": "unknown",
        "last_update": None,
        "error": "Status file not found",
    }

    try:
        if not status_file.exists():
            return default_status

        with open(status_file, "r") as f:
            status_data = json.load(f)

        # Check if the status is recent (within last 5 minutes)
        if status_data.get("last_update"):
            last_update = datetime.fromisoformat(status_data["last_update"])
            now = datetime.now()

            # Handle timezone-aware/naive datetime comparison
            if last_update.tzinfo is None:
                last_update = last_update.replace(tzinfo=now.tzinfo)
            elif now.tzinfo is None:
                now = now.replace(tzinfo=last_update.tzinfo)

            time_diff = (now - last_update).total_seconds()

            daemon_update_interval = status_data.get(
                "update_interval", 300
            )  # Default to 5 minutes if not set

            # Consider daemon stale if no update in <daemon_update_interval> minutes
            if time_diff > daemon_update_interval:
                status_data["running"] = False
                status_data["status"] = "stale"
                status_data["error"] = f"No update for {int(time_diff)} seconds"
            else:
                status_data["status"] = (
                    "active" if status_data.get("running", False) else "stopped"
                )
        else:
            status_data["status"] = "unknown"

        return status_data

    except json.JSONDecodeError as e:
        return {
            "running": False,
            "status": "error",
            "error": f"Invalid status file format: {e}",
        }
    except Exception as e:
        return {
            "running": False,
            "status": "error",
            "error": f"Error reading status: {e}",
        }


def fetch_new_data():
    switchbot_token = os.getenv("SWITCHBOT_TOKEN", "")
    switchbot_secret = os.getenv("SWITCHBOT_SECRET", "")
    switchbot = SwitchBot(switchbot_token, switchbot_secret)
    living_room_mac = os.getenv("LIVING_ROOM_MAC", "D40E84863006")
    bedroom_mac = os.getenv("BEDROOM_MAC", "D40E84861814")
    office_mac = os.getenv("OFFICE_MAC", "D628EA1C498F")
    outdoor_mac = os.getenv("OUTDOOR_MAC", "D40E84064570")

    devices = {
        "Living Room": living_room_mac,
        "Bedroom": bedroom_mac,
        "Office": office_mac,
        "Outdoor": outdoor_mac,
    }

    for location, mac in devices.items():
        try:
            device = switchbot.device(id=mac)
            if device is None:
                print(f"Device with MAC {mac} not found.")
                continue

            device_status = device.status()
            if device_status is None or "temperature" not in device_status:
                print(f"Could not retrieve data from device {mac}.")
                continue

            temperature = device_status.get("temperature")
            humidity = device_status.get("humidity")

            # Save to database
            temp_record = Temperature(
                timestamp=timezone.now(),
                location=location,
                temperature=temperature,
                humidity=humidity,
            )
            temp_record.save()
            print(f"Saved data for {location}: {temperature}°C, {humidity}%")
        except Exception as e:
            print(f"Error fetching data from device {mac}: {e}")


def home(request):
    return render(request, "homepage/home.html", {})


def basic(request):
    living_temp = (
        Temperature.objects.filter(location="Living Room")
        .order_by("-timestamp")
        .first()
    )
    bedroom_temp = (
        Temperature.objects.filter(location="Bedroom").order_by("-timestamp").first()
    )
    office_temp = (
        Temperature.objects.filter(location="Office").order_by("-timestamp").first()
    )
    outdoor_temp = (
        Temperature.objects.filter(location="Outdoor").order_by("-timestamp").first()
    )

    temeperature_data = [
        {
            "location": "Living Room",
            "temperature": living_temp.temperature if living_temp else None,
            "timestamp": living_temp.timestamp if living_temp else None,
            "humidity": living_temp.humidity if living_temp else None,
        },
        {
            "location": "Bedroom",
            "temperature": bedroom_temp.temperature if bedroom_temp else None,
            "timestamp": bedroom_temp.timestamp if bedroom_temp else None,
            "humidity": bedroom_temp.humidity if bedroom_temp else None,
        },
        {
            "location": "Office",
            "temperature": office_temp.temperature if office_temp else None,
            "timestamp": office_temp.timestamp if office_temp else None,
            "humidity": office_temp.humidity if office_temp else None,
        },
        {
            "location": "Outdoor",
            "temperature": outdoor_temp.temperature if outdoor_temp else None,
            "timestamp": outdoor_temp.timestamp if outdoor_temp else None,
            "humidity": outdoor_temp.humidity if outdoor_temp else None,
        },
    ]
    return render(
        request, "homepage/basic.html", {"temeperature_data": temeperature_data}
    )


def temeperature_data(request):
    """Get current temperature data for each location (most recent reading per location)"""
    # Check if this is a manual refresh request
    manual_refresh = request.GET.get("manual", "").lower() == "true"

    if manual_refresh:
        # Manual refresh: fetch new data from SwitchBot devices first
        try:
            fetch_new_data()
        except Exception as e:
            print(f"Error fetching new data from devices: {e}")
            # Continue with database data even if device fetch fails

    # Always return the latest data from database
    # Fix: Use a more robust approach to get distinct locations
    current_data = []

    # Get unique locations first using a more reliable method
    # unique_locations = set(
    #     Temperature.objects.values_list('location', flat=True))

    unique_locations = ["Living Room", "Bedroom", "Office", "Outdoor"]

    for location in unique_locations:
        latest = (
            Temperature.objects.filter(location=location).order_by("-timestamp").first()
        )
        if latest:
            current_data.append(
                {
                    "pk": latest.pk,
                    "timestamp": latest.timestamp.isoformat(),
                    "location": latest.location,
                    "temperature": latest.temperature,
                    "humidity": latest.humidity,
                }
            )

    return JsonResponse(current_data, safe=False)


def historical_data(request):
    """Get historical temperature data for the last 24 hours"""
    hours = int(request.GET.get("hours", 24))
    since = timezone.now() - timedelta(hours=hours)

    readings = Temperature.objects.filter(timestamp__gte=since).order_by("timestamp")

    # Group data by location
    data_by_location = {}
    for reading in readings:
        if reading.location not in data_by_location:
            data_by_location[reading.location] = []

        data_by_location[reading.location].append(
            {
                "timestamp": reading.timestamp.isoformat(),
                "temperature": reading.temperature,
                "humidity": reading.humidity,
            }
        )

    return JsonResponse(data_by_location, safe=False)


def daemon_status(request):
    """Get the current status of the temperature daemon."""
    status = get_daemon_status()
    return JsonResponse(status, safe=False)


def system_status(request):
    """Get comprehensive system status including daemon and recent data."""
    daemon_status_data = get_daemon_status()

    # Get recent temperature data count
    recent_cutoff = timezone.now() - timedelta(hours=1)
    recent_readings_count = Temperature.objects.filter(
        timestamp__gte=recent_cutoff
    ).count()

    # Get last reading timestamp
    last_reading = Temperature.objects.order_by("-timestamp").first()
    last_reading_time = last_reading.timestamp.isoformat() if last_reading else None

    # Get total readings count
    total_readings = Temperature.objects.count()

    system_status_data = {
        "daemon": daemon_status_data,
        "database": {
            "total_readings": total_readings,
            "recent_readings_count": recent_readings_count,
            "last_reading_time": last_reading_time,
            "database_size": Temperature.objects.count(),
        },
        "system": {
            "timestamp": timezone.now().isoformat(),
            "status": (
                "healthy"
                if daemon_status_data.get("running", False)
                and recent_readings_count > 0
                else "warning"
            ),
        },
    }

    return JsonResponse(system_status_data, safe=False)
