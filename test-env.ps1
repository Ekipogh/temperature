# Test Environment Variables Script
# This script helps verify that environment variables are properly set before running Docker Compose

param(
    [switch]$ShowValues = $false
)

function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "⚠️ $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Info { param($Message) Write-Host "ℹ️ $Message" -ForegroundColor Cyan }

# Load environment variables from .env file
function Import-EnvFile {
    param([string]$EnvFile = ".env")

    if (-not (Test-Path $EnvFile)) {
        Write-Warning "Environment file $EnvFile not found"
        return $false
    }

    try {
        Get-Content $EnvFile | ForEach-Object {
            if ($_ -match '^\s*([^#][^=]*?)\s*=\s*(.*?)\s*$') {
                $name = $matches[1]
                $value = $matches[2]
                # Remove quotes if present
                $value = $value -replace '^["''](.*?)["'']$', '$1'
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
        return $true
    } catch {
        Write-Error "Error loading environment file: $($_.Exception.Message)"
        return $false
    }
}

Write-Info "Testing Environment Variable Configuration..."

# Check if .env file exists
if (Test-Path ".env") {
    Write-Success ".env file found"

    # Load environment variables
    if (Import-EnvFile) {
        Write-Success "Environment variables loaded from .env file"
    } else {
        Write-Error "Failed to load environment variables"
        exit 1
    }
} else {
    Write-Warning ".env file not found - checking if variables are already set"
}

# Required environment variables
$requiredVars = @(
    "SWITCHBOT_TOKEN",
    "SWITCHBOT_SECRET",
    "LIVING_ROOM_MAC",
    "BEDROOM_MAC",
    "OFFICE_MAC",
    "OUTDOOR_MAC"
)

$optionalVars = @(
    "TEMPERATURE_INTERVAL",
    "ENVIRONMENT",
    "DATABASE_PATH"
)

Write-Info "`nChecking required environment variables..."
$missingVars = @()

foreach ($var in $requiredVars) {
    $value = [Environment]::GetEnvironmentVariable($var)
    if ([string]::IsNullOrEmpty($value)) {
        Write-Error "$var is not set"
        $missingVars += $var
    } else {
        if ($ShowValues) {
            # Show first few characters for security
            $maskedValue = $value.Substring(0, [Math]::Min(4, $value.Length)) + "..."
            Write-Success "$var = $maskedValue"
        } else {
            Write-Success "$var is set"
        }
    }
}

Write-Info "`nChecking optional environment variables..."
foreach ($var in $optionalVars) {
    $value = [Environment]::GetEnvironmentVariable($var)
    if ([string]::IsNullOrEmpty($value)) {
        Write-Warning "$var is not set (optional)"
    } else {
        if ($ShowValues) {
            Write-Success "$var = $value"
        } else {
            Write-Success "$var is set"
        }
    }
}

if ($missingVars.Count -gt 0) {
    Write-Error "`nMissing required environment variables: $($missingVars -join ', ')"
    Write-Info "Please set these variables in your .env file or system environment"
    exit 1
} else {
    Write-Success "`nAll required environment variables are set!"
    Write-Info "You can now run: docker-compose -f ci/docker-compose.preprod.yml up --build -d"
}

# Test docker-compose config
Write-Info "`nTesting Docker Compose configuration..."
try {
    $configTest = docker-compose -f ci/docker-compose.preprod.yml config 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker Compose configuration is valid"
    } else {
        Write-Error "Docker Compose configuration error:"
        Write-Host $configTest -ForegroundColor Red
    }
} catch {
    Write-Warning "Could not test Docker Compose configuration: $($_.Exception.Message)"
}

Write-Info "`nEnvironment variable test completed!"