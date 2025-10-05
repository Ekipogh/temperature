#!/bin/bash
set -e  # Exit on any error

port=$1

# Ensure we're using the virtual environment
export PATH="/home/app/venv/bin:$PATH"

# Change to app directory
cd /app

# Apply database migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn server
echo "Starting Gunicorn server on port $port..."
exec gunicorn temperature.wsgi:application --bind 0.0.0.0:$port --workers 3