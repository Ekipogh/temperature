#!/bin/bash
set -e  # Exit on any error
set -x  # Print commands as they are executed

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
echo "Starting Gunicorn server on port 8000..."
exec gunicorn temperature.wsgi:application --bind 0.0.0.0:8000 --workers 3