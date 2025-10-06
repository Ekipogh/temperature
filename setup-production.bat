@echo off
REM Setup script for Temperature Monitoring System - Production Environment
REM This script creates the necessary directories on the Windows host for Docker bind mounts

echo Setting up Temperature Monitoring System - Production Environment
echo.

REM Create data directory for SQLite database
echo Creating data directory: C:\temperature\data
if not exist "C:\temperature\data" (
    mkdir "C:\temperature\data"
    echo Created: C:\temperature\data
) else (
    echo Already exists: C:\temperature\data
)

REM Create logs directory for daemon logs
echo Creating logs directory: C:\temperature\logs
if not exist "C:\temperature\logs" (
    mkdir "C:\temperature\logs"
    echo Created: C:\temperature\logs
) else (
    echo Already exists: C:\temperature\logs
)

echo.
echo Setup complete! The following directories are ready:
echo - C:\temperature\data (for SQLite database)
echo - C:\temperature\logs (for application logs)
echo.
echo Next steps:
echo 1. Create a .env file in the project root with your SwitchBot credentials
echo 2. Run: docker-compose -f ci/docker-compose.production.yml up -d
echo.
echo Your SQLite database will be accessible at: C:\temperature\data\db.sqlite3
echo.
pause