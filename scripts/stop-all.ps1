# =============================================================================
# NEXI AI CMDB - Stop All Services
# =============================================================================
# Usage: .\scripts\stop-all.ps1
# =============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Red
Write-Host "   NEXI AI CMDB - Stopping Services    " -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""

# Stop Backend on port 8000
Write-Host "[1/2] Stopping Backend API (port 8000)..." -ForegroundColor Yellow
$backend = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($backend) {
    $backend | ForEach-Object { 
        taskkill /F /PID $_.OwningProcess 2>$null
    }
    Write-Host "      Backend stopped." -ForegroundColor Green
}
else {
    Write-Host "      Backend not running." -ForegroundColor Gray
}

# Stop React Frontend on port 3002
Write-Host "[2/2] Stopping React Frontend (port 3002)..." -ForegroundColor Yellow
$frontend = Get-NetTCPConnection -LocalPort 3002 -State Listen -ErrorAction SilentlyContinue
if ($frontend) {
    $frontend | ForEach-Object { 
        taskkill /F /PID $_.OwningProcess 2>$null
    }
    Write-Host "      Frontend stopped." -ForegroundColor Green
}
else {
    Write-Host "      Frontend not running." -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   All Services Stopped!               " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
