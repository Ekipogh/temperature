# Temperature Daemon Docker Setup

This document explains how to use the preproduction Docker setup for the temperature daemon.

## Overview

The temperature daemon Docker setup includes:
- Automated repository cloning/copying
- Python virtual environment creation
- Dependency installation
- Database volume mounting for sharing with the main Django app
- Health checks and proper logging

## Prerequisites

1. Docker and Docker Compose installed
2. Your repository accessible (either local copy or Git repository)
3. Environment variables configured in `.env` file

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# SwitchBot API Configuration
SWITCHBOT_TOKEN=your_switchbot_token_here
SWITCHBOT_SECRET=your_switchbot_secret_here

# Daemon Configuration
TEMPERATURE_INTERVAL=600         # Check interval in seconds (10 minutes)
RATE_LIMIT_SLEEP_TIME=300       # Rate limit sleep time in seconds (5 minutes)

# Django Configuration
DJANGO_SETTINGS_MODULE=temperature.settings
SECRET_KEY=your_django_secret_key
DEBUG=False

# Database Configuration (if using PostgreSQL instead of SQLite)
# DATABASE_URL=postgresql://user:password@db:5432/temperature_db
```

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Build and start all services:**
   ```bash
   cd ci/
   docker-compose -f docker-compose.preprod.yml up --build -d
   ```

2. **View logs:**
   ```bash
   # Daemon logs
   docker-compose -f docker-compose.preprod.yml logs -f temperature-daemon
   
   # All services logs
   docker-compose -f docker-compose.preprod.yml logs -f
   ```

3. **Stop services:**
   ```bash
   docker-compose -f docker-compose.preprod.yml down
   ```

### Option 2: Using Docker directly

1. **Build the image:**
   ```bash
   docker build -f ci/preprod_daemon.dockerfile -t temperature-daemon:preprod .
   ```

2. **Create a shared volume:**
   ```bash
   docker volume create temperature_data
   ```

3. **Run the container:**
   ```bash
   docker run -d \
     --name temperature_daemon_preprod \
     --restart unless-stopped \
     -v temperature_data:/app/data \
     -v $(pwd)/.env:/app/.env:ro \
     -e DJANGO_SETTINGS_MODULE=temperature.settings \
     temperature-daemon:preprod
   ```

4. **View logs:**
   ```bash
   docker logs -f temperature_daemon_preprod
   ```

## Database Volume Sharing

The key feature of this setup is the shared database volume (`temperature_data`):

- **Daemon container**: Mounts volume at `/app/data`
- **Django app container**: Mounts the same volume at `/app/data`
- **Database file**: Located at `/app/data/db.sqlite3` (or configured path)

This allows both containers to access the same database file safely.

## Health Checks

The container includes health checks that:
- Monitor if the daemon process is running
- Check every 30 seconds
- Allow 30 seconds startup time
- Retry 3 times before marking as unhealthy

Check health status:
```bash
docker ps  # Shows health status in STATUS column
docker inspect temperature_daemon_preprod --format='{{.State.Health.Status}}'
```

## Troubleshooting

### Container won't start
1. Check if `.env` file exists and has proper permissions
2. Verify Docker volume permissions
3. Check logs: `docker logs temperature_daemon_preprod`

### Database issues
1. Ensure volume is properly mounted
2. Check Django migrations are applied
3. Verify database file permissions

### Daemon not collecting data
1. Check SwitchBot API credentials in `.env`
2. Verify internet connectivity
3. Check rate limiting settings
4. Review daemon logs for API errors

### Common Commands

```bash
# Enter container shell for debugging
docker exec -it temperature_daemon_preprod /bin/bash

# Restart the daemon
docker restart temperature_daemon_preprod

# Update the image
docker-compose -f docker-compose.preprod.yml pull
docker-compose -f docker-compose.preprod.yml up -d

# Clean up volumes (WARNING: This deletes data!)
docker-compose -f docker-compose.preprod.yml down -v
```

## Production Considerations

For production deployment, consider:

1. **Use Git clone instead of COPY** in Dockerfile
2. **Set up proper secrets management** instead of .env files
3. **Use external database** (PostgreSQL) instead of SQLite
4. **Configure log rotation** and centralized logging
5. **Set up monitoring and alerting**
6. **Use multi-stage builds** to reduce image size
7. **Implement proper backup strategy** for data volumes

## Customization

### Using Git Clone

To clone from a Git repository instead of copying local files, modify the Dockerfile:

```dockerfile
# Replace this line in the Dockerfile:
COPY . .

# With:
RUN git clone https://github.com/your-username/new_temperature.git .
```

### Custom Intervals

Modify environment variables in docker-compose.yml or .env:

```yaml
environment:
  - TEMPERATURE_INTERVAL=300  # 5 minutes
  - RATE_LIMIT_SLEEP_TIME=180  # 3 minutes
```