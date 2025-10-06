# Docker Environment Variables Fix

## Problem
The `.env` file was being mounted from Windows host to Linux containers with corrupted permissions (`-?????????`), making it inaccessible inside the containers.

## Root Cause
- Windows file system permissions don't translate properly to Linux containers
- Docker volume mounting of individual files from Windows to Linux can cause permission issues
- The mounted `.env` file becomes unreadable inside the container

## Solution
Instead of mounting the `.env` file, we now pass environment variables directly to the containers through Docker Compose's `environment` section.

### Changes Made:

1. **Updated `ci/docker-compose.preprod.yml`**:
   - Removed `.env` file volume mounts
   - Added explicit environment variables using `${VARIABLE_NAME}` syntax
   - Docker Compose will read these from the host environment

2. **Updated `deploy-windows.ps1`**:
   - Added `Import-EnvFile` function to load `.env` file into PowerShell environment
   - Variables are automatically passed to docker-compose

3. **Updated CI/CD workflow**:
   - Sets environment variables directly instead of creating `.env` file
   - Uses `$env:GITHUB_ENV` to persist variables across workflow steps

4. **Added `test-env.ps1`**:
   - Utility script to verify environment variables are properly set
   - Tests Docker Compose configuration validity

## How It Works Now:

### Manual Deployment:
```powershell
# Load .env file into PowerShell environment
.\deploy-windows.ps1 -Action start
# OR manually:
# 1. Load variables from .env
# 2. Run: docker-compose -f ci/docker-compose.preprod.yml up --build -d
```

### CI/CD Deployment:
```yaml
# Set environment variables from secrets
- name: Set environment variables
  run: |
    $env:SWITCHBOT_TOKEN = "${{ secrets.SWITCHBOT_TOKEN }}"
    # ... other variables

# Variables are automatically passed to docker-compose
- name: Deploy
  run: docker-compose -f ci/docker-compose.preprod.yml up --build -d
```

## Testing:
```powershell
# Test environment variable setup
.\test-env.ps1

# Show variable values (first 4 chars only for security)
.\test-env.ps1 -ShowValues

# Test Docker Compose configuration
docker-compose -f ci/docker-compose.preprod.yml config
```

## Benefits:
- ✅ No file permission issues
- ✅ Works consistently across Windows/Linux
- ✅ More secure (no .env file in container)
- ✅ Easier CI/CD integration
- ✅ Better debugging with test script

## Verification:
After deployment, you can verify environment variables are set correctly:
```powershell
# Check variables inside container
docker-compose -f ci/docker-compose.preprod.yml exec django-app env | grep SWITCHBOT
docker-compose -f ci/docker-compose.preprod.yml exec temperature-daemon env | grep SWITCHBOT
```