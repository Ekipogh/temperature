import json
from datetime import timedelta
from django.db import models
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

from homepage.models import Temperature


def device_detail(request, device_name):
    """Display detailed statistics for a specific device/location."""
    # Normalize device name to match database location format
    location_map = {
        'living-room': 'Living Room',
        'bedroom': 'Bedroom',
        'office': 'Office',
        'outdoor': 'Outdoor'
    }

    location = location_map.get(device_name.lower(), device_name.replace('-', ' ').title())

    # Check if the location exists in the database
    if not Temperature.objects.filter(location=location).exists():
        # Return a 404 if no data exists for this location
        raise Http404(f"No temperature data found for location: {location}")

    # Get current time for calculations
    now = timezone.now()

    # Calculate time ranges
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(days=1)
    one_week_ago = now - timedelta(weeks=1)
    one_month_ago = now - timedelta(days=30)

    # Get latest reading
    latest_reading = Temperature.objects.filter(location=location).first()

    # Calculate averages for different time periods
    hourly_avg = Temperature.objects.filter(
        location=location,
        timestamp__gte=one_hour_ago
    ).aggregate(
        avg_temp=models.Avg('temperature'),
        avg_humidity=models.Avg('humidity'),
        count=models.Count('id')
    )

    daily_avg = Temperature.objects.filter(
        location=location,
        timestamp__gte=one_day_ago
    ).aggregate(
        avg_temp=models.Avg('temperature'),
        avg_humidity=models.Avg('humidity'),
        count=models.Count('id')
    )

    weekly_avg = Temperature.objects.filter(
        location=location,
        timestamp__gte=one_week_ago
    ).aggregate(
        avg_temp=models.Avg('temperature'),
        avg_humidity=models.Avg('humidity'),
        count=models.Count('id')
    )

    monthly_avg = Temperature.objects.filter(
        location=location,
        timestamp__gte=one_month_ago
    ).aggregate(
        avg_temp=models.Avg('temperature'),
        avg_humidity=models.Avg('humidity'),
        count=models.Count('id')
    )

    # Get min/max values for different periods
    daily_extremes = Temperature.objects.filter(
        location=location,
        timestamp__gte=one_day_ago
    ).aggregate(
        min_temp=models.Min('temperature'),
        max_temp=models.Max('temperature'),
        min_humidity=models.Min('humidity'),
        max_humidity=models.Max('humidity')
    )

    weekly_extremes = Temperature.objects.filter(
        location=location,
        timestamp__gte=one_week_ago
    ).aggregate(
        min_temp=models.Min('temperature'),
        max_temp=models.Max('temperature'),
        min_humidity=models.Min('humidity'),
        max_humidity=models.Max('humidity')
    )

    # Get hourly data for the last 24 hours for detailed chart
    hourly_data = []
    for i in range(24):
        hour_start = now - timedelta(hours=i+1)
        hour_end = now - timedelta(hours=i)

        hour_avg = Temperature.objects.filter(
            location=location,
            timestamp__gte=hour_start,
            timestamp__lt=hour_end
        ).aggregate(
            avg_temp=models.Avg('temperature'),
            avg_humidity=models.Avg('humidity'),
            count=models.Count('id')
        )

        hourly_data.append({
            'hour': hour_start.strftime('%H:%M'),
            'timestamp': hour_start.isoformat(),
            'avg_temp': round(hour_avg['avg_temp'], 1) if hour_avg['avg_temp'] else None,
            'avg_humidity': round(hour_avg['avg_humidity'], 1) if hour_avg['avg_humidity'] else None,
            'count': hour_avg['count']
        })

    # Reverse to get chronological order
    hourly_data.reverse()

    # Get daily data for the last 7 days
    daily_data = []
    for i in range(7):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        day_avg = Temperature.objects.filter(
            location=location,
            timestamp__gte=day_start,
            timestamp__lt=day_end
        ).aggregate(
            avg_temp=models.Avg('temperature'),
            avg_humidity=models.Avg('humidity'),
            min_temp=models.Min('temperature'),
            max_temp=models.Max('temperature'),
            count=models.Count('id')
        )

        daily_data.append({
            'date': day_start.strftime('%m/%d'),
            'full_date': day_start.strftime('%Y-%m-%d'),
            'day_name': day_start.strftime('%A'),
            'avg_temp': round(day_avg['avg_temp'], 1) if day_avg['avg_temp'] else None,
            'avg_humidity': round(day_avg['avg_humidity'], 1) if day_avg['avg_humidity'] else None,
            'min_temp': round(day_avg['min_temp'], 1) if day_avg['min_temp'] else None,
            'max_temp': round(day_avg['max_temp'], 1) if day_avg['max_temp'] else None,
            'count': day_avg['count']
        })

    # Reverse to get chronological order
    daily_data.reverse()

    # Get recent readings for timeline
    recent_readings = Temperature.objects.filter(
        location=location
    ).order_by('-timestamp')[:20]

    # Calculate total statistics
    total_stats = Temperature.objects.filter(location=location).aggregate(
        total_count=models.Count('id'),
        avg_temp=models.Avg('temperature'),
        avg_humidity=models.Avg('humidity'),
        min_temp=models.Min('temperature'),
        max_temp=models.Max('temperature'),
        min_humidity=models.Min('humidity'),
        max_humidity=models.Max('humidity')
    )

    # Get first and last reading dates
    first_reading = Temperature.objects.filter(location=location).order_by('timestamp').first()

    context = {
        'device_name': device_name,
        'location': location,
        'latest_reading': latest_reading,
        'hourly_avg': hourly_avg,
        'daily_avg': daily_avg,
        'weekly_avg': weekly_avg,
        'monthly_avg': monthly_avg,
        'daily_extremes': daily_extremes,
        'weekly_extremes': weekly_extremes,
        'hourly_data': hourly_data,
        'daily_data': daily_data,
        'hourly_data_json': json.dumps(hourly_data),
        'daily_data_json': json.dumps(daily_data),
        'recent_readings': recent_readings,
        'total_stats': total_stats,
        'first_reading': first_reading,
        'data_age_days': (now - first_reading.timestamp).days if first_reading else 0,
    }

    return render(request, 'device/device.html', context)
