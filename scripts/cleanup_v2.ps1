<#
.SYNOPSIS
    Nexi AI CMDB V2 - Cleanup Script
.DESCRIPTION
    Stops all V2 containers, removes volumes (-v), removes networks, and kills V2 Backend/Frontend processes.
    WARNING: DELETES ALL V2 DATA.
#>

Write-Host "=================================================================" -ForegroundColor Red
Write-Host "   NEXI AI CMDB V2 - FULL CLEANUP (DELETE EVERYTHING)" -ForegroundColor Red
Write-Host "=================================================================" -ForegroundColor Red

# 1. Load Config to know ports/project details
$EnvFile = "$PSScriptRoot\..\.env.v2"
if (-not (Test-Path $EnvFile)) {
    Write-Warning "Configuration file .env.v2 not found. Proceeding with defaults/assumptions might differ."
    # We proceed anyway to try cleaning up based on compose file
}

# 2. Docker Compose Down (with Volumes)
Write-Host "`n[STEP 1] Removing Docker Containers & Volumes..." -ForegroundColor Yellow
$ComposeFile = "$PSScriptRoot\..\docker-lab\docker-compose-v2.yml"
docker-compose -f $ComposeFile --env-file $EnvFile down -v --remove-orphans

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Docker V2 Environment removed." -ForegroundColor Green
}
else {
    Write-Host "❌ Docker cleanup failed (or nothing to clean)." -ForegroundColor Red
}

# 3. Kill Processes (Backend/Frontend V2)
Write-Host "`n[STEP 2] Killing V2 Processes..." -ForegroundColor Yellow

# Function to kill process by port
# Function to stop process by port (renamed to use approved verb 'Stop')
function Stop-ProcessByPort($port, $name) {
    if (-not $port) { return }
    $ProcId = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -First 1
    if ($ProcId) {
        Write-Host "Stopping $name on port $port (PID: $ProcId)..." -ForegroundColor Red
        Stop-Process -Id $ProcId -Force -ErrorAction SilentlyContinue
    }
    else {
        Write-Host "$name process not found (Port $port is free)." -ForegroundColor Gray
    }
}

# Load ports from env if available, else assume defaults
$BackendPort = 9000
$FrontendPort = 4002

if (Test-Path $EnvFile) {
    # Use foreach loop to avoid pipeline variable scoping issues
    foreach ($line in Get-Content $EnvFile) {
        if ($line -match "^BACKEND_PORT=(\d+)") {
            $BackendPort = $Matches[1]
        }
        if ($line -match "^FRONTEND_PORT=(\d+)") {
            $FrontendPort = $Matches[1]
        }
    }
}

Stop-ProcessByPort $BackendPort "Backend V2"
Stop-ProcessByPort $FrontendPort "Frontend V2"

Write-Host "`n[CLEANUP COMPLETED] V2 System is gone." -ForegroundColor Green
Write-Host "You can now test clean installation with setup_v2.ps1" -ForegroundColor Cyan
