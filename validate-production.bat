@echo off
REM Validation script for Temperature Monitoring System - Production Environment
REM This script checks if the production setup is working correctly

echo Validating Temperature Monitoring System - Production Environment
echo.

REM Check if required directories exist
echo Checking required directories...
if exist "C:\temperature\data" (
    echo [OK] C:\temperature\data exists
) else (
    echo [ERROR] C:\temperature\data does not exist
    echo Please run setup-production.bat first
    goto :end
)

if exist "C:\temperature\logs" (
    echo [OK] C:\temperature\logs exists
) else (
    echo [ERROR] C:\temperature\logs does not exist
    echo Please run setup-production.bat first
    goto :end
)

REM Check if .env file exists
if exist ".env" (
    echo [OK] .env file exists
) else (
    echo [WARNING] .env file not found
    echo Please copy .env.production.template to .env and configure it
)

echo.
echo Checking Docker Compose configuration...
docker-compose -f ci/docker-compose.production.yml config > nul 2>&1
if %ERRORLEVEL% == 0 (
    echo [OK] Docker Compose configuration is valid
) else (
    echo [ERROR] Docker Compose configuration has issues
    echo Please check ci/docker-compose.production.yml
    goto :end
)

echo.
echo Checking if containers are running...
docker-compose -f ci/docker-compose.production.yml ps --filter "status=running" | findstr "django_app_production" > nul
if %ERRORLEVEL% == 0 (
    echo [OK] Django app container is running
    echo Testing web interface...
    curl -s -o nul -w "%%{http_code}" http://localhost:7000 | findstr "200" > nul
    if %ERRORLEVEL% == 0 (
        echo [OK] Web interface is accessible at http://localhost:7000
    ) else (
        echo [WARNING] Web interface may not be fully ready yet
    )
) else (
    echo [INFO] Django app container is not running
    echo To start: docker-compose -f ci/docker-compose.production.yml up -d
)

docker-compose -f ci/docker-compose.production.yml ps --filter "status=running" | findstr "temperature_daemon_production" > nul
if %ERRORLEVEL% == 0 (
    echo [OK] Temperature daemon container is running
) else (
    echo [INFO] Temperature daemon container is not running
    echo To start: docker-compose -f ci/docker-compose.production.yml up -d
)

echo.
echo Checking database file...
if exist "C:\temperature\data\db.sqlite3" (
    echo [OK] Database file exists at C:\temperature\data\db.sqlite3
) else (
    echo [INFO] Database file not yet created (will be created on first run)
)

echo.
echo Validation complete!
echo.

:end
pause