# Temperature Monitor - Windows Deployment Script
# This script sets up and deploys the temperature monitoring application on Windows

param(
    [Parameter(HelpMessage="Action to perform: setup, start, stop, restart, status, logs")]
    [ValidateSet("setup", "start", "stop", "restart", "status", "logs", "clean")]
    [string]$Action = "status",

    [Parameter(HelpMessage="Follow logs in real-time")]
    [switch]$Follow
)

# Color output functions
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "⚠️ $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Info { param($Message) Write-Host "ℹ️ $Message" -ForegroundColor Cyan }

# Check if Docker is available
function Test-DockerAvailable {
    try {
        $null = docker --version 2>$null
        return $true
    } catch {
        return $false
    }
}

# Check if Docker Desktop is running
function Test-DockerRunning {
    try {
        $null = docker info 2>$null
        return $true
    } catch {
        return $false
    }
}

# Setup function
function Invoke-Setup {
    Write-Info "Setting up Temperature Monitor on Windows..."

    # Check Docker
    if (-not (Test-DockerAvailable)) {
        Write-Error "Docker is not installed or not in PATH"
        Write-Info "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/"
        exit 1
    }

    if (-not (Test-DockerRunning)) {
        Write-Warning "Docker Desktop is not running. Starting it..."
        try {
            Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -ErrorAction Stop
            Write-Info "Waiting for Docker Desktop to start..."

            $timeout = 60
            $elapsed = 0
            do {
                Start-Sleep -Seconds 5
                $elapsed += 5
                Write-Host "." -NoNewline

                if ($elapsed -ge $timeout) {
                    Write-Error "Timeout waiting for Docker Desktop to start"
                    exit 1
                }
            } while (-not (Test-DockerRunning))

            Write-Success "Docker Desktop is now running"
        } catch {
            Write-Error "Could not start Docker Desktop: $($_.Exception.Message)"
            exit 1
        }
    }

    # Check if .env file exists
    if (-not (Test-Path ".env")) {
        Write-Warning ".env file not found"
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Write-Info "Created .env file from .env.example"
            Write-Warning "Please edit .env file with your actual SwitchBot credentials"
            Write-Info "You can edit it with: notepad .env"
        } else {
            Write-Error ".env.example file not found. Please create .env file manually"
        }
    } else {
        Write-Success ".env file exists"
    }

    Write-Success "Setup completed!"
    Write-Info "To start the application, run: .\deploy-windows.ps1 -Action start"
}

# Start function
function Invoke-Start {
    Write-Info "Starting Temperature Monitor services..."

    if (-not (Test-DockerRunning)) {
        Write-Error "Docker Desktop is not running. Please start it first or run setup."
        exit 1
    }

    try {
        Write-Info "Building and starting containers..."
        docker-compose -f ci/docker-compose.preprod.yml up --build -d

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Services started successfully"

            Write-Info "Waiting for services to be ready..."
            Start-Sleep -Seconds 15

            # Check service status
            Invoke-Status

            Write-Success "Temperature Monitor is running!"
            Write-Info "Django Web Interface: http://localhost:7070"

        } else {
            Write-Error "Failed to start services"
            exit 1
        }
    } catch {
        Write-Error "Error starting services: $($_.Exception.Message)"
        exit 1
    }
}

# Stop function
function Invoke-Stop {
    Write-Info "Stopping Temperature Monitor services..."

    try {
        docker-compose -f ci/docker-compose.preprod.yml down
        Write-Success "Services stopped successfully"
    } catch {
        Write-Error "Error stopping services: $($_.Exception.Message)"
    }
}

# Restart function
function Invoke-Restart {
    Write-Info "Restarting Temperature Monitor services..."
    Invoke-Stop
    Start-Sleep -Seconds 5
    Invoke-Start
}

# Status function
function Invoke-Status {
    Write-Info "Checking Temperature Monitor status..."

    if (-not (Test-DockerRunning)) {
        Write-Warning "Docker Desktop is not running"
        return
    }

    try {
        Write-Info "Container Status:"
        docker-compose -f ci/docker-compose.preprod.yml ps

        Write-Info "`nChecking Django app..."
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:7070/" -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Success "Django app is responding on port 7070"
            }
        } catch {
            Write-Warning "Django app is not responding: $($_.Exception.Message)"
        }

        Write-Info "`nChecking daemon status..."
        try {
            $daemonStatus = docker-compose -f ci/docker-compose.preprod.yml exec -T temperature-daemon cat /app/data/daemon_status.json 2>$null
            if ($daemonStatus) {
                Write-Success "Daemon status file accessible"
                # Parse and display key info
                $status = $daemonStatus | ConvertFrom-Json
                Write-Info "Daemon running: $($status.running)"
                Write-Info "Last check: $($status.last_check)"
                Write-Info "Total readings: $($status.total_readings)"
            }
        } catch {
            Write-Warning "Could not access daemon status"
        }

    } catch {
        Write-Error "Error checking status: $($_.Exception.Message)"
    }
}

# Logs function
function Invoke-Logs {
    Write-Info "Displaying Temperature Monitor logs..."

    try {
        if ($Follow) {
            Write-Info "Following logs (Press Ctrl+C to stop)..."
            docker-compose -f ci/docker-compose.preprod.yml logs -f
        } else {
            docker-compose -f ci/docker-compose.preprod.yml logs
        }
    } catch {
        Write-Error "Error displaying logs: $($_.Exception.Message)"
    }
}

# Clean function
function Invoke-Clean {
    Write-Warning "This will remove all containers, volumes, and images for Temperature Monitor"
    $confirmation = Read-Host "Are you sure? (y/N)"

    if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
        Write-Info "Cleaning up..."
        try {
            docker-compose -f ci/docker-compose.preprod.yml down -v --remove-orphans
            docker system prune -f
            Write-Success "Cleanup completed"
        } catch {
            Write-Error "Error during cleanup: $($_.Exception.Message)"
        }
    } else {
        Write-Info "Cleanup cancelled"
    }
}

# Main execution
switch ($Action) {
    "setup" { Invoke-Setup }
    "start" { Invoke-Start }
    "stop" { Invoke-Stop }
    "restart" { Invoke-Restart }
    "status" { Invoke-Status }
    "logs" { Invoke-Logs }
    "clean" { Invoke-Clean }
    default {
        Write-Info "Temperature Monitor Windows Deployment Script"
        Write-Info "Usage: .\deploy-windows.ps1 -Action <action>"
        Write-Info "Actions: setup, start, stop, restart, status, logs, clean"
        Write-Info "Example: .\deploy-windows.ps1 -Action start"
        Write-Info "For logs: .\deploy-windows.ps1 -Action logs -Follow"
    }
}