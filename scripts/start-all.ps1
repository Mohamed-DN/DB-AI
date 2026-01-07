# =============================================================================
# NEXI AI CMDB - Start All Services
# =============================================================================
# Usage: .\scripts\start-all.ps1
# =============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   NEXI AI CMDB - Starting Services    " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = "c:\AI-Nexi\Nexi_DB_AI"

# Refresh PATH for Node.js
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

# 1. Start Backend API (port 8000)
Write-Host "[1/2] Starting Backend API (port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot\WebInterface\backend'; Write-Host 'Backend API - Port 8000' -ForegroundColor Green; python main.py"
Start-Sleep -Seconds 3

# 2. Start React Frontend (port 3002)
Write-Host "[2/2] Starting React Frontend (port 3002)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot\WebInterface\frontend-react'; Write-Host 'React Frontend - Port 3002' -ForegroundColor Green; npm run dev"
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   All Services Started!               " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access Points:" -ForegroundColor Cyan
Write-Host "  - React Dashboard: http://localhost:3002" -ForegroundColor White
Write-Host "  - Backend API:     http://localhost:8000" -ForegroundColor White
Write-Host "  - Mongo Express:   http://localhost:8081" -ForegroundColor Gray
Write-Host "  - Old Frontend:    http://localhost:3000" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Enter to open dashboard..." -ForegroundColor Gray
Read-Host
Start-Process "http://localhost:3002"
