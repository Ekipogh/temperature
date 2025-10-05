# Docker Deployment Guide

This guide covers deploying the Temperature Monitor system using Docker containers.

## Overview

The Docker deployment consists of two main services:
- **Django Application**: Web dashboard and API endpoints
- **Temperature Daemon**: Background data collection service

Both services share a common database and configuration through Docker volumes.

## Prerequisites

- Docker and Docker Compose installed
- `.env` file with SwitchBot credentials
- Basic understanding of Docker concepts

## Quick Start

1. **Clone and prepare environment**
   ```bash
   git clone <repository-url>
   cd temperature
   cp .env.example .env
   # Edit .env with your SwitchBot credentials
   ```

2. **Deploy pre-production environment**
   ```bash
   cd ci
   docker-compose -f docker-compose.preprod.yml up -d
   ```

3. **Access the dashboard**
   - Pre-production: http://localhost:7070

## Architecture

### Service Overview

| Service | Container Name | Purpose | Port |
|---------|---------------|---------|------|
| django-app | django_app_preprod | Web dashboard & API | 7070 |
| temperature-daemon | temperature_daemon_preprod | Data collection | - |

### Data Flow

```
SwitchBot Devices → Temperature Daemon → SQLite Database → Django API → Web Dashboard
```

### Volume Mapping

- `temperature_data`: Shared database storage (`/app/data`)
- `temperature_logs`: Daemon logs (`/app/logs`)
- `.env` file: Environment configuration (read-only)

## Configuration

### Environment Variables

The following environment variables are used across both containers:

#### Required Variables
```env
# SwitchBot API Credentials
SWITCHBOT_TOKEN=your_token_here
SWITCHBOT_SECRET=your_secret_here

# Device MAC Addresses
LIVING_ROOM_MAC=D40E84863006
BEDROOM_MAC=D40E84861814
OFFICE_MAC=D628EA1C498F
OUTDOOR_MAC=D40E84064570
```

#### Daemon-Specific Variables
```env
# Data Collection Settings
TEMPERATURE_INTERVAL=600        # Collection interval (seconds)
RATE_LIMIT_SLEEP_TIME=300      # Rate limit backoff (seconds)

# Database Configuration
DATABASE_PATH=/app/data/db.sqlite3  # Database location in container

# Environment Identification
ENVIRONMENT=preprod            # Environment name
```

### Docker Compose Configuration

The `docker-compose.preprod.yml` file defines:

- **Network isolation**: `temperature_network`
- **Automatic restarts**: `unless-stopped`
- **Health checks**: Monitor daemon process
- **Volume persistence**: Data survives container restarts
- **Service dependencies**: Django app waits for daemon

## Operations

### Starting Services

```bash
# Start all services in background
docker-compose -f ci/docker-compose.preprod.yml up -d

# Start specific service
docker-compose -f ci/docker-compose.preprod.yml up -d django-app
```

### Monitoring

```bash
# Check service status
docker-compose -f ci/docker-compose.preprod.yml ps

# View all logs
docker-compose -f ci/docker-compose.preprod.yml logs -f

# View specific service logs
docker-compose -f ci/docker-compose.preprod.yml logs -f temperature-daemon
docker-compose -f ci/docker-compose.preprod.yml logs -f django-app

# Check container health
docker inspect temperature_daemon_preprod | grep -A 10 "Health"
```

### Management

```bash
# Restart services
docker-compose -f ci/docker-compose.preprod.yml restart

# Stop services
docker-compose -f ci/docker-compose.preprod.yml stop

# Remove containers (keeps volumes)
docker-compose -f ci/docker-compose.preprod.yml down

# Remove containers and volumes (⚠️ DELETES DATA)
docker-compose -f ci/docker-compose.preprod.yml down -v
```

### Updates and Maintenance

```bash
# Rebuild and restart
docker-compose -f ci/docker-compose.preprod.yml build
docker-compose -f ci/docker-compose.preprod.yml up -d

# Execute commands in running containers
docker exec -it django_app_preprod python manage.py shell
docker exec -it temperature_daemon_preprod cat /app/daemon_status.json
```

## Data Management

### Database Access

```bash
# Django shell
docker exec -it django_app_preprod python manage.py shell

# Database backup
docker exec django_app_preprod python backup_utility.py create

# View database files
docker exec django_app_preprod ls -la /app/data/
```

### Log Management

```bash
# View daemon logs
docker exec temperature_daemon_preprod tail -f /app/logs/temperature_daemon.log

# Copy logs to host
docker cp temperature_daemon_preprod:/app/logs/ ./host-logs/
```

## Health Monitoring

### Automatic Health Checks

The daemon container includes health checks that:
- Monitor the daemon process every 30 seconds
- Restart container if daemon stops responding
- Provide startup grace period of 30 seconds

### Manual Health Verification

```bash
# Check daemon status
docker exec temperature_daemon_preprod cat /app/daemon_status.json

# Verify data collection
docker exec django_app_preprod python manage.py shell -c "
from homepage.models import Temperature;
print(f'Total readings: {Temperature.objects.count()}');
print(f'Latest: {Temperature.objects.latest('timestamp')}')"

# Test API endpoints
curl http://localhost:7070/api/temperature/
```

## Troubleshooting

### Common Issues

**Container won't start**
```bash
# Check logs for errors
docker-compose -f ci/docker-compose.preprod.yml logs service-name

# Check container status
docker-compose -f ci/docker-compose.preprod.yml ps

# Rebuild container
docker-compose -f ci/docker-compose.preprod.yml build service-name
```

**Database issues**
```bash
# Check database file exists
docker exec django_app_preprod ls -la /app/data/

# Run migrations
docker exec django_app_preprod python manage.py migrate

# Check database permissions
docker exec django_app_preprod ls -la /app/data/db.sqlite3
```

**Network issues**
```bash
# Check port conflicts
netstat -tulpn | grep :7070

# Test container connectivity
docker exec django_app_preprod curl http://localhost:8000/api/temperature/
```

**Environment variables**
```bash
# Check loaded environment
docker exec django_app_preprod printenv | grep SWITCHBOT
docker exec temperature_daemon_preprod printenv | grep TEMPERATURE
```

### Performance Optimization

**Resource monitoring**
```bash
# Check resource usage
docker stats

# View container processes
docker exec django_app_preprod ps aux
docker exec temperature_daemon_preprod ps aux
```

**Log rotation**
```bash
# Configure Docker log rotation in daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

## Security Considerations

- Containers run as non-root user (`app`)
- Environment file mounted read-only
- Network isolation between containers
- No unnecessary ports exposed
- Regular security updates via base image updates

## Backup Strategy

```bash
# Create complete backup
docker exec django_app_preprod python backup_utility.py create

# Backup Docker volumes
docker run --rm -v temperature_temperature_data:/data -v $(pwd):/backup alpine tar czf /backup/data-backup.tar.gz -C /data .

# Backup configuration
cp .env .env.backup
cp ci/docker-compose.preprod.yml docker-compose.backup.yml
```

## Production Considerations

For production deployment, consider:

1. **SSL/TLS termination** with reverse proxy (nginx, traefik)
2. **Environment-specific configurations** for different stages
3. **Log aggregation** (ELK stack, Fluentd)
4. **Monitoring and alerting** (Prometheus, Grafana)
5. **Automated backups** with retention policies
6. **Resource limits** and scaling strategies
7. **Security hardening** and vulnerability scanning

---

For additional support, refer to the main [README.md](../README.md) or create an issue in the repository.