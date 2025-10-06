# Setup script for Temperature Monitoring System - Production Environment
# This script creates the necessary directories on the Windows host for Docker bind mounts

Write-Host "Setting up Temperature Monitoring System - Production Environment" -ForegroundColor Green
Write-Host ""

# Create data directory for SQLite database
$dataPath = "C:\temperature\data"
Write-Host "Creating data directory: $dataPath"
if (-not (Test-Path $dataPath)) {
    New-Item -ItemType Directory -Path $dataPath -Force | Out-Null
    Write-Host "Created: $dataPath" -ForegroundColor Green
} else {
    Write-Host "Already exists: $dataPath" -ForegroundColor Yellow
}

# Create logs directory for daemon logs
$logsPath = "C:\temperature\logs"
Write-Host "Creating logs directory: $logsPath"
if (-not (Test-Path $logsPath)) {
    New-Item -ItemType Directory -Path $logsPath -Force | Out-Null
    Write-Host "Created: $logsPath" -ForegroundColor Green
} else {
    Write-Host "Already exists: $logsPath" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup complete! The following directories are ready:" -ForegroundColor Green
Write-Host "- C:\temperature\data (for SQLite database)" -ForegroundColor Cyan
Write-Host "- C:\temperature\logs (for application logs)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Create a .env file in the project root with your SwitchBot credentials"
Write-Host "2. Run: docker-compose -f ci/django-compose.production.yml up -d"
Write-Host ""
Write-Host "Your SQLite database will be accessible at: C:\temperature\data\db.sqlite3" -ForegroundColor Magenta
Write-Host ""
Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") | Out-Null