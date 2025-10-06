# Production Deployment Guide

This guide covers deploying the Temperature Monitoring System in production using Docker Compose with SQLite database stored on the host Windows machine.

> **Note**: This deployment uses the **same dockerfiles** as preprod for consistency. See `DOCKER_UNIFIED_GUIDE.md` for details on how the unified Docker strategy works.

## Quick Start

### 1. Setup Host Directories
Run the setup script to create required directories:

**Option A: PowerShell (Recommended)**
```powershell
.\setup-production.ps1
```

**Option B: Command Prompt**
```cmd
setup-production.bat
```

**Option C: Manual Setup**
```cmd
mkdir C:\temperature\data
mkdir C:\temperature\logs
```

### 2. Configure Environment Variables
Create a `.env` file in the project root:

```cmd
copy .env.production.template .env
```

Edit `.env` and fill in your SwitchBot credentials and device MAC addresses.

### 3. Start the Services
```cmd
docker-compose -f ci/django-compose.production.yml up -d
```

### 4. Access the Application
- **Web Interface**: http://localhost:7000
- **Database File**: `C:\temperature\data\db.sqlite3`
- **Logs**: `C:\temperature\logs\`

## File Locations

### On Host Windows Machine:
- **Database**: `C:\temperature\data\db.sqlite3`
- **Logs**: `C:\temperature\logs\`
- **Configuration**: `.env` (in project root)

### In Docker Containers:
- **Database**: `/app/data/db.sqlite3`
- **Logs**: `/app/logs/`

## Management Commands

### View Logs
```cmd
# View Django app logs
docker-compose -f ci/django-compose.production.yml logs django-app

# View daemon logs
docker-compose -f ci/django-compose.production.yml logs temperature-daemon

# Follow logs in real-time
docker-compose -f ci/django-compose.production.yml logs -f
```

### Stop Services
```cmd
docker-compose -f ci/django-compose.production.yml down
```

### Restart Services
```cmd
docker-compose -f ci/django-compose.production.yml restart
```

### Update Services
```cmd
# Pull latest changes and rebuild
docker-compose -f ci/django-compose.production.yml down
docker-compose -f ci/django-compose.production.yml build --no-cache
docker-compose -f ci/django-compose.production.yml up -d
```

## Database Access

Since the SQLite database is stored on the host machine, you can:

1. **Backup the database**:
   ```cmd
   copy "C:\temperature\data\db.sqlite3" "C:\temperature\backup\db_backup_%date%.sqlite3"
   ```

2. **Access with SQLite tools**:
   - Use DB Browser for SQLite
   - Command line: `sqlite3 C:\temperature\data\db.sqlite3`

3. **Django management commands**:
   ```cmd
   # Run migrations
   docker-compose -f ci/django-compose.production.yml exec django-app python manage.py migrate

   # Create superuser
   docker-compose -f ci/django-compose.production.yml exec django-app python manage.py createsuperuser

   # Access Django shell
   docker-compose -f ci/django-compose.production.yml exec django-app python manage.py shell
   ```

## Troubleshooting

### Check Container Status
```cmd
docker-compose -f ci/django-compose.production.yml ps
```

### Check Container Health
```cmd
docker-compose -f ci/django-compose.production.yml exec temperature-daemon pgrep -f temperature_daemon.py
```

### Verify Database Permissions
Ensure the Docker containers can read/write to the host directories:
```cmd
# Check if directories exist and are accessible
dir C:\temperature\data
dir C:\temperature\logs
```

### View Environment Variables
```cmd
docker-compose -f ci/django-compose.production.yml exec django-app env | findstr DJANGO
docker-compose -f ci/django-compose.production.yml exec temperature-daemon env | findstr SWITCHBOT
```

## Security Notes

- The `.env` file contains sensitive credentials - do not commit it to version control
- Consider using Docker secrets for production deployments
- Ensure proper file permissions on the host directories
- Regularly backup your database file

## Monitoring

- **Health Checks**: The daemon service includes health checks that verify the process is running
- **Logs**: All application logs are available in `C:\temperature\logs\`
- **Status**: Check daemon status via the web interface or status file at `C:\temperature\data\daemon_status.json`