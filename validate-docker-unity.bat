@echo off
REM Docker Unified Configuration Validator
REM This script validates that both preprod and production use the same dockerfiles

echo Docker Unified Configuration Validator
echo =====================================
echo.

echo Checking dockerfile references in Docker Compose files...
echo.

REM Check preprod configuration
echo [PREPROD] Dockerfiles used:
findstr /n "dockerfile:" ci\docker-compose.preprod.yml | findstr /v "#"

echo.

REM Check production configuration
echo [PRODUCTION] Dockerfiles used:
findstr /n "dockerfile:" ci\django-compose.production.yml | findstr /v "#"

echo.

REM Verify the dockerfiles exist
echo Verifying dockerfile existence:
if exist "ci\django.dockerfile" (
    echo [OK] ci\django.dockerfile exists
) else (
    echo [ERROR] ci\django.dockerfile missing
)

if exist "ci\preprod_daemon.dockerfile" (
    echo [OK] ci\preprod_daemon.dockerfile exists
) else (
    echo [ERROR] ci\preprod_daemon.dockerfile missing
)

echo.

REM Check for any orphaned dockerfiles
echo Checking for orphaned dockerfiles:
if exist "ci\production_daemon.dockerfile" (
    echo [WARNING] ci\production_daemon.dockerfile exists but is not needed
    echo [INFO] Production now uses ci\preprod_daemon.dockerfile
) else (
    echo [OK] No orphaned production dockerfile found
)

echo.

REM Validate Docker Compose syntax
echo Validating Docker Compose configurations:
docker-compose -f ci/docker-compose.preprod.yml config > nul 2>&1
if %ERRORLEVEL% == 0 (
    echo [OK] Preprod configuration is valid
) else (
    echo [ERROR] Preprod configuration has issues
)

docker-compose -f ci/django-compose.production.yml config > nul 2>&1
if %ERRORLEVEL% == 0 (
    echo [OK] Production configuration is valid
) else (
    echo [ERROR] Production configuration has issues
)

echo.
echo Validation complete!
echo.
echo Summary:
echo - Both environments use the same dockerfiles for consistency
echo - Differentiation happens via environment variables and Docker Compose settings
echo - See DOCKER_UNIFIED_GUIDE.md for detailed information
echo.
pause