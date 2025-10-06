@echo off
REM Comprehensive Production Deployment Validation Script
REM This script validates all aspects of the production deployment

echo ==========================================
echo Production Deployment Validation Script
echo ==========================================
echo.

set ERROR_COUNT=0

echo [1/8] Checking Host Directory Structure...
echo ----------------------------------------
if exist "C:\temperature\data" (
    echo [OK] C:\temperature\data exists
) else (
    echo [ERROR] C:\temperature\data does not exist - run setup-production.ps1
    set /a ERROR_COUNT+=1
)

if exist "C:\temperature\logs" (
    echo [OK] C:\temperature\logs exists
) else (
    echo [ERROR] C:\temperature\logs does not exist - run setup-production.ps1
    set /a ERROR_COUNT+=1
)

echo.
echo [2/8] Checking Configuration Files...
echo ------------------------------------
if exist ".env" (
    echo [OK] .env file exists
    findstr /C:"DJANGO_DEBUG" .env > nul
    if %ERRORLEVEL% == 0 (
        echo [OK] DJANGO_DEBUG configured
    ) else (
        echo [WARNING] DJANGO_DEBUG not found in .env
    )

    findstr /C:"DJANGO_ALLOWED_HOSTS" .env > nul
    if %ERRORLEVEL% == 0 (
        echo [OK] DJANGO_ALLOWED_HOSTS configured
    ) else (
        echo [WARNING] DJANGO_ALLOWED_HOSTS not found in .env
    )

    findstr /C:"SWITCHBOT_TOKEN" .env > nul
    if %ERRORLEVEL% == 0 (
        echo [OK] SWITCHBOT_TOKEN configured
    ) else (
        echo [ERROR] SWITCHBOT_TOKEN not found in .env
        set /a ERROR_COUNT+=1
    )
) else (
    echo [ERROR] .env file not found - copy from .env.production.template
    set /a ERROR_COUNT+=1
)

if exist "temperature\production_settings.py" (
    echo [OK] Production settings file exists
) else (
    echo [ERROR] Production settings file missing
    set /a ERROR_COUNT+=1
)

echo.
echo [3/8] Checking Docker Configuration...
echo ------------------------------------
docker-compose -f ci/django-compose.production.yml config > nul 2>&1
if %ERRORLEVEL% == 0 (
    echo [OK] Docker Compose configuration is valid
) else (
    echo [ERROR] Docker Compose configuration has syntax errors
    set /a ERROR_COUNT+=1
)

echo.
echo [4/8] Checking Required Dockerfiles...
echo ------------------------------------
if exist "ci\django.dockerfile" (
    echo [OK] Django dockerfile exists
) else (
    echo [ERROR] ci\django.dockerfile missing
    set /a ERROR_COUNT+=1
)

if exist "ci\daemon.dockerfile" (
    echo [OK] Daemon dockerfile exists
) else (
    echo [ERROR] ci\daemon.dockerfile missing
    set /a ERROR_COUNT+=1
)

if exist "startup.sh" (
    echo [OK] Django startup script exists
) else (
    echo [ERROR] startup.sh missing
    set /a ERROR_COUNT+=1
)

echo.
echo [5/8] Checking Port Availability...
echo ---------------------------------
netstat -ano | findstr :7000 > nul
if %ERRORLEVEL% == 0 (
    echo [WARNING] Port 7000 is already in use - may conflict with production deployment
) else (
    echo [OK] Port 7000 is available
)

echo.
echo [6/8] Checking Docker Service...
echo ------------------------------
docker version > nul 2>&1
if %ERRORLEVEL% == 0 (
    echo [OK] Docker is running
) else (
    echo [ERROR] Docker is not running or not installed
    set /a ERROR_COUNT+=1
)

echo.
echo [7/8] Checking Production Containers (if running)...
echo -------------------------------------------------
docker-compose -f ci/django-compose.production.yml ps --filter "status=running" | findstr "django_app_production" > nul
if %ERRORLEVEL% == 0 (
    echo [OK] Django production container is running

    REM Test web interface
    curl -s -o nul -w "%%{http_code}" http://localhost:7000 2>nul | findstr "200" > nul
    if %ERRORLEVEL% == 0 (
        echo [OK] Web interface responding on http://localhost:7000
    ) else (
        echo [WARNING] Web interface not responding - container may still be starting
    )
) else (
    echo [INFO] Django production container not running
)

docker-compose -f ci/django-compose.production.yml ps --filter "status=running" | findstr "temperature_daemon_production" > nul
if %ERRORLEVEL% == 0 (
    echo [OK] Temperature daemon production container is running
) else (
    echo [INFO] Temperature daemon production container not running
)

echo.
echo [8/8] Checking Database and Logs...
echo ---------------------------------
if exist "C:\temperature\data\db.sqlite3" (
    echo [OK] Production database file exists
    for %%A in ("C:\temperature\data\db.sqlite3") do echo [INFO] Database size: %%~zA bytes
) else (
    echo [INFO] Production database not yet created (will be created on first run)
)

if exist "C:\temperature\logs\django.log" (
    echo [OK] Django log file exists
) else (
    echo [INFO] Django log file not yet created
)

echo.
echo ==========================================
echo Validation Summary
echo ==========================================

if %ERROR_COUNT% == 0 (
    echo [SUCCESS] All critical checks passed! Production deployment is ready.
    echo.
    echo Next steps:
    echo 1. Review any warnings above
    echo 2. Start services: docker-compose -f ci/django-compose.production.yml up -d
    echo 3. Access web interface: http://localhost:7000
    echo 4. Monitor logs: docker-compose -f ci/django-compose.production.yml logs -f
) else (
    echo [FAILURE] %ERROR_COUNT% critical issues found. Please fix before deployment.
    echo.
    echo Common fixes:
    echo - Run: setup-production.ps1
    echo - Copy: .env.production.template to .env and configure
    echo - Ensure Docker is running
)

echo.
echo Detailed deployment guide: PRODUCTION_REVIEW.md
echo.
pause