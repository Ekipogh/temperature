# Docker Configuration Guide

This document explains how the Temperature Monitoring System uses **the same dockerfiles** for both preprod and production environments, with differences only in the Docker Compose configurations.

## Unified Dockerfile Strategy

### ✅ **Same Dockerfiles, Different Configurations**

We use the same dockerfiles for both environments to ensure consistency and reduce maintenance overhead:

| Service | Dockerfile | Used In |
|---------|------------|---------|
| Django Web App | `ci/django.dockerfile` | Both preprod & production |
| Temperature Daemon | `ci/preprod_daemon.dockerfile` | Both preprod & production |

### 🔧 **How It Works**

The differentiation between environments happens at the **Docker Compose level**, not the Dockerfile level:

1. **Same Base Images**: Both environments use identical Python base images and dependencies
2. **Environment Variables**: Different `ENVIRONMENT` values trigger different behavior
3. **Volume Mounting**: Different volume strategies (Docker volumes vs host bind mounts)
4. **Port Mapping**: Different ports to avoid conflicts
5. **Container Names**: Different names for identification

## Docker Compose Configurations

### 📋 **Environment Comparison**

| Aspect | Preprod | Production |
|--------|---------|------------|
| **Dockerfile** | `ci/django.dockerfile` | `ci/django.dockerfile` |
| **Daemon Dockerfile** | `ci/preprod_daemon.dockerfile` | `ci/preprod_daemon.dockerfile` |
| **Environment Variable** | `ENVIRONMENT=preprod` | `ENVIRONMENT=production` |
| **Database Storage** | Docker volume | Host bind mount |
| **Web Port** | `7070:8000` | `7000:8000` |
| **Container Names** | `*_preprod` | `*_production` |

### 🔄 **Environment-Specific Behavior**

The application automatically adapts based on the `ENVIRONMENT` variable:

```python
# In services/switchbot_service.py
def get_switchbot_service() -> SwitchBotService:
    is_preprod = os.getenv("ENVIRONMENT", "production").lower() == "preprod"

    if is_preprod:
        return PreProdSwitchBotService()  # Returns mock data
    else:
        return SwitchBotService()         # Connects to real SwitchBot API
```

## File Structure

```
ci/
├── django.dockerfile              # ✅ Used by both environments
├── preprod_daemon.dockerfile      # ✅ Used by both environments
├── docker-compose.preprod.yml     # Preprod configuration
└── django-compose.production.yml  # Production configuration
```

## Usage Examples

### 🧪 **Preprod Environment**
```bash
# Start preprod (uses Docker volumes)
docker-compose -f ci/docker-compose.preprod.yml up -d

# Access: http://localhost:7070
# Uses mock SwitchBot data
```

### 🚀 **Production Environment**
```bash
# Setup host directories first
mkdir C:\temperature\data
mkdir C:\temperature\logs

# Start production (uses host bind mounts)
docker-compose -f ci/django-compose.production.yml up -d

# Access: http://localhost:7000
# Uses real SwitchBot API
```

## Benefits of This Approach

### ✅ **Advantages**

1. **Consistency**: Same base images ensure identical runtime environments
2. **Maintenance**: Only need to maintain two dockerfiles instead of four
3. **Testing**: What works in preprod will work in production
4. **Updates**: Update dependencies once, applies to both environments
5. **Security**: Same security patches across environments

### 🔧 **Configuration Management**

| Configuration Type | Handled By | Examples |
|-------------------|------------|----------|
| **Runtime Behavior** | Environment Variables | `ENVIRONMENT`, `DATABASE_PATH` |
| **Infrastructure** | Docker Compose | Ports, volumes, networks |
| **Secrets** | `.env` files | SwitchBot credentials |

## Development Workflow

### 🔄 **Typical Workflow**

1. **Develop**: Test locally with development settings
2. **Preprod**: Test in preprod environment with mock data
3. **Production**: Deploy to production with real API connections

### 🛠 **Making Changes**

```bash
# Update both environments simultaneously
docker-compose -f ci/docker-compose.preprod.yml build --no-cache
docker-compose -f ci/django-compose.production.yml build --no-cache

# Or use a script to update both
```

## Environment Variable Reference

### 🔑 **Shared Variables** (used by both environments)
```env
DJANGO_SETTINGS_MODULE=temperature.settings
DATABASE_PATH=/app/data/db.sqlite3
DAEMON_STATUS_FILE=/app/data/daemon_status.json
TEMPERATURE_INTERVAL=600
RATE_LIMIT_SLEEP_TIME=300
```

### 🎯 **Environment-Specific Variables**
```env
# Preprod
ENVIRONMENT=preprod

# Production
ENVIRONMENT=production
```

### 🔐 **Credentials** (production only)
```env
SWITCHBOT_TOKEN=your_token_here
SWITCHBOT_SECRET=your_secret_here
LIVING_ROOM_MAC=your_mac_address
# ... etc
```

## Best Practices

### ✅ **Do**
- Use the same dockerfiles for consistency
- Differentiate through environment variables
- Test in preprod before production deployment
- Keep Docker Compose files in sync for common settings

### ❌ **Don't**
- Create separate dockerfiles unless absolutely necessary
- Hard-code environment-specific values in dockerfiles
- Skip preprod testing
- Mix development dependencies in production images

## Troubleshooting

### 🔍 **Common Issues**

1. **Wrong Environment**: Check `ENVIRONMENT` variable is set correctly
2. **Port Conflicts**: Ensure preprod (7070) and production (7000) use different ports
3. **Volume Issues**: Production needs host directories created first
4. **Service Selection**: Application automatically selects service based on environment

### 🛠 **Debugging Commands**

```bash
# Check environment variables
docker-compose -f ci/django-compose.production.yml exec django-app env | grep ENVIRONMENT

# Verify service selection
docker-compose -f ci/django-compose.production.yml logs django-app | grep "SwitchBot service"

# Check container differences
docker-compose -f ci/docker-compose.preprod.yml ps
docker-compose -f ci/django-compose.production.yml ps
```

This unified approach ensures consistency while maintaining the flexibility to configure each environment appropriately for its specific use case.