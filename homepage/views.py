import os
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from homepage.models import Temperature
from switchbot import SwitchBot


def fetch_new_data():
    switchbot_token = os.getenv('SWITCHBOT_TOKEN', '')
    switchbot_secret = os.getenv('SWITCHBOT_SECRET', '')
    switchbot = SwitchBot(switchbot_token, switchbot_secret)
    living_room_mac = os.getenv('LIVING_ROOM_MAC', 'D40E84863006')
    bedroom_mac = os.getenv('BEDROOM_MAC', 'D40E84861814')
    office_mac = os.getenv('OFFICE_MAC', 'D628EA1C498F')
    outdoor_mac = os.getenv('OUTDOOR_MAC', 'D40E84064570')

    devices = {
        'Living Room': living_room_mac,
        'Bedroom': bedroom_mac,
        'Office': office_mac,
        'Outdoor': outdoor_mac
    }

    for location, mac in devices.items():
        try:
            device = switchbot.device(id=mac)
            if device is None:
                print(f"Device with MAC {mac} not found.")
                continue

            device_status = device.status()
            if device_status is None or 'temperature' not in device_status:
                print(f"Could not retrieve data from device {mac}.")
                continue

            temperature = device_status.get('temperature')
            humidity = device_status.get('humidity')

            # Save to database
            temp_record = Temperature(
                timestamp=timezone.now(),
                location=location,
                temperature=temperature,
                humidity=humidity
            )
            temp_record.save()
            print(f"Saved data for {location}: {temperature}°C, {humidity}%")
        except Exception as e:
            print(f"Error fetching data from device {mac}: {e}")


def home(request):
    return render(request, 'homepage/home.html', {})


def basic(request):
    living_temp = Temperature.objects.filter(
        location='Living Room').order_by('-timestamp').first()
    bedroom_temp = Temperature.objects.filter(
        location='Bedroom').order_by('-timestamp').first()
    office_temp = Temperature.objects.filter(
        location='Office').order_by('-timestamp').first()
    outdoor_temp = Temperature.objects.filter(
        location='Outdoor').order_by('-timestamp').first()

    temeperature_data = [
        {'location': 'Living Room', 'temperature': living_temp.temperature if living_temp else None,
            'timestamp': living_temp.timestamp if living_temp else None, "humidity": living_temp.humidity if living_temp else None},
        {'location': 'Bedroom', 'temperature': bedroom_temp.temperature if bedroom_temp else None,
            'timestamp': bedroom_temp.timestamp if bedroom_temp else None, "humidity": bedroom_temp.humidity if bedroom_temp else None},
        {'location': 'Office', 'temperature': office_temp.temperature if office_temp else None,
         'timestamp': office_temp.timestamp if office_temp else None, "humidity": office_temp.humidity if office_temp else None},
        {'location': 'Outdoor', 'temperature': outdoor_temp.temperature if outdoor_temp else None,
         'timestamp': outdoor_temp.timestamp if outdoor_temp else None, "humidity": outdoor_temp.humidity if outdoor_temp else None}
    ]
    return render(request, 'homepage/basic.html', {'temeperature_data': temeperature_data})


def temeperature_data(request):
    """Get current temperature data for each location (most recent reading per location)"""
    # Check if this is a manual refresh request
    manual_refresh = request.GET.get('manual', '').lower() == 'true'

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
        latest = Temperature.objects.filter(
            location=location).order_by('-timestamp').first()
        if latest:
            current_data.append({
                'pk': latest.pk,
                'timestamp': latest.timestamp.isoformat(),
                'location': latest.location,
                'temperature': latest.temperature,
                'humidity': latest.humidity
            })

    return JsonResponse(current_data, safe=False)


def historical_data(request):
    """Get historical temperature data for the last 24 hours"""
    hours = int(request.GET.get('hours', 24))
    since = timezone.now() - timedelta(hours=hours)

    readings = Temperature.objects.filter(
        timestamp__gte=since
    ).order_by('timestamp')

    # Group data by location
    data_by_location = {}
    for reading in readings:
        if reading.location not in data_by_location:
            data_by_location[reading.location] = []

        data_by_location[reading.location].append({
            'timestamp': reading.timestamp.isoformat(),
            'temperature': reading.temperature,
            'humidity': reading.humidity
        })

    return JsonResponse(data_by_location, safe=False)
