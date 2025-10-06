# Host Machine Docker Setup Guide

## Prerequisites

1. **Docker and Docker Compose installed** on your host machine
2. **Git repository cloned** to your host machine
3. **Environment variables configured**

## Setup Steps

### 1. Install Docker (if not already installed)

**Windows:**
- Download Docker Desktop from https://www.docker.com/products/docker-desktop/
- Follow installation instructions
- Ensure WSL2 is enabled (if on Windows)
- Verify installation: Open PowerShell and run `docker --version`

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

### 2. Clone and Navigate to Project

**Windows (PowerShell):**
```powershell
git clone <your-repo-url>
cd temperature
```

**Linux/Mac (Bash):**
```bash
git clone <your-repo-url>
cd temperature
```

### 3. Create Environment File

**Windows (PowerShell):**
```powershell
# Copy from example
Copy-Item .env.example .env

# Edit with your actual values
notepad .env  # or use your preferred editor
```

**Linux/Mac (Bash):**
```bash
# Copy from example
cp .env.example .env

# Edit with your actual values
nano .env  # or use your preferred editor
```

Your `.env` should contain:
```
SWITCHBOT_TOKEN=your_actual_token_here
SWITCHBOT_SECRET=your_actual_secret_here
LIVING_ROOM_MAC=D40E84863006
BEDROOM_MAC=D40E84861814
OFFICE_MAC=D628EA1C498F
OUTDOOR_MAC=D40E84064570
TEMPERATURE_INTERVAL=60
ENVIRONMENT=preprod
DATABASE_PATH=/app/data/db.sqlite3
```

### 4. Run with Docker Compose

**Windows (PowerShell):**
```powershell
# Build and start all services
docker-compose -f ci/docker-compose.preprod.yml up --build -d

# Check status
docker-compose -f ci/docker-compose.preprod.yml ps

# View logs
docker-compose -f ci/docker-compose.preprod.yml logs -f

# Stop services
docker-compose -f ci/docker-compose.preprod.yml down
```

**Linux/Mac (Bash):**
```bash
# Build and start all services
docker-compose -f ci/docker-compose.preprod.yml up --build -d

# Check status
docker-compose -f ci/docker-compose.preprod.yml ps

# View logs
docker-compose -f ci/docker-compose.preprod.yml logs -f

# Stop services
docker-compose -f ci/docker-compose.preprod.yml down
```

### 5. Access Your Application

- **Django Web Interface**: http://localhost:7070
- **Database**: Stored in Docker volume `temperature_data`
- **Logs**: Available via `docker-compose logs` or in volume `temperature_logs`

### 6. Useful Commands

**Windows (PowerShell):**
```powershell
# Restart specific service
docker-compose -f ci/docker-compose.preprod.yml restart temperature-daemon

# Update code and rebuild
git pull
docker-compose -f ci/docker-compose.preprod.yml down
docker-compose -f ci/docker-compose.preprod.yml up --build -d

# Check daemon status
docker-compose -f ci/docker-compose.preprod.yml exec temperature-daemon cat /app/data/daemon_status.json

# Access Django shell
docker-compose -f ci/docker-compose.preprod.yml exec django-app python manage.py shell

# View database
docker-compose -f ci/docker-compose.preprod.yml exec django-app python manage.py dbshell

# Check what's using port 7070
Get-NetTCPConnection -LocalPort 7070 -ErrorAction SilentlyContinue
```

**Linux/Mac (Bash):**
```bash
# Restart specific service
docker-compose -f ci/docker-compose.preprod.yml restart temperature-daemon

# Update code and rebuild
git pull
docker-compose -f ci/docker-compose.preprod.yml down
docker-compose -f ci/docker-compose.preprod.yml up --build -d

# Check daemon status
docker-compose -f ci/docker-compose.preprod.yml exec temperature-daemon cat /app/data/daemon_status.json

# Access Django shell
docker-compose -f ci/docker-compose.preprod.yml exec django-app python manage.py shell

# View database
docker-compose -f ci/docker-compose.preprod.yml exec django-app python manage.py dbshell

# Check what's using port 7070
sudo netstat -tulpn | grep 7070
```

## Troubleshooting

### Common Issues:

1. **Port 7070 already in use**:

   **Windows:**
   ```powershell
   # Check what's using the port
   Get-NetTCPConnection -LocalPort 7070 -ErrorAction SilentlyContinue
   # Or change the port in docker-compose.preprod.yml
   ```

   **Linux:**
   ```bash
   # Check what's using the port
   sudo netstat -tulpn | grep 7070
   # Or change the port in docker-compose.preprod.yml
   ```

2. **Permission issues with volumes**:

   **Windows:**
   ```powershell
   # Fix volume permissions
   docker-compose -f ci/docker-compose.preprod.yml down
   docker volume rm temperature_data temperature_logs
   docker-compose -f ci/docker-compose.preprod.yml up --build -d
   ```

   **Linux:**
   ```bash
   # Fix volume permissions
   docker-compose -f ci/docker-compose.preprod.yml down
   docker volume rm temperature_data temperature_logs
   docker-compose -f ci/docker-compose.preprod.yml up --build -d
   ```

3. **Environment variables not loading**:
   - Ensure `.env` file is in the project root
   - **Windows**: Check file with `Get-Content .env`
   - **Linux**: Check file with `cat .env`
   - Verify encoding is UTF-8 (especially on Windows)

4. **Docker Desktop not running (Windows)**:
   ```powershell
   # Start Docker Desktop
   Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

   # Wait for Docker to be ready
   do {
       Start-Sleep -Seconds 5
       $dockerRunning = docker info 2>$null
   } while (-not $dockerRunning)
   ```

5. **Services not starting**:

   **Windows:**
   ```powershell
   # Check logs for errors
   docker-compose -f ci/docker-compose.preprod.yml logs

   # Check individual service logs
   docker-compose -f ci/docker-compose.preprod.yml logs temperature-daemon
   docker-compose -f ci/docker-compose.preprod.yml logs django-app
   ```

   **Linux:**
   ```bash
   # Check logs for errors
   docker-compose -f ci/docker-compose.preprod.yml logs

   # Check individual service logs
   docker-compose -f ci/docker-compose.preprod.yml logs temperature-daemon
   docker-compose -f ci/docker-compose.preprod.yml logs django-app
   ```## Production Deployment

For production, use a similar approach but:
1. Create `docker-compose.prod.yml` with production configurations
2. Use proper secrets management (Docker Secrets, Kubernetes Secrets, etc.)
3. Set up reverse proxy (nginx) for SSL/TLS
4. Configure backup strategies for the database volume
5. Set up monitoring and alerting