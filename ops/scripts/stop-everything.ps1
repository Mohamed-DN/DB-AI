# =============================================================================
# NEXI AI CMDB - HARD STOP EVERYTHING
# =============================================================================
# Stops Backend, Frontend, and ALL Docker Containers.
# =============================================================================

Write-Host ""
Write-Host "🛑 STOPPING EVERYTHING (APPS + DOCKER)..." -ForegroundColor Red
Write-Host ""

# 1. Stop Web Services (Port 8000 & 3002)
Write-Host "[1/3] Stopping Web Services..." -ForegroundColor Yellow
$ports = @(8000, 3002)
foreach ($p in $ports) {
    $proc = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
    if ($proc) {
        $proc | ForEach-Object { taskkill /F /PID $_.OwningProcess 2>$null }
        Write-Host "      Port $p freed." -ForegroundColor DarkGray
    }
}

# 2. Stop Python Agents
Write-Host "[2/3] Stopping Python Agents..." -ForegroundColor Yellow
taskkill /F /IM python.exe 2>$null
Write-Host "      All Python processes killed." -ForegroundColor DarkGray

# 3. Stop Docker Containers
Write-Host "[3/3] Stopping Docker Containers..." -ForegroundColor Yellow
Write-Host "      Stopping MongoDB Stack..." -ForegroundColor DarkGray
cd "c:\AI-Nexi\Nexi_DB_AI\MongoDB"
docker compose stop

Write-Host "      Stopping Lab Stack..." -ForegroundColor DarkGray
cd "c:\AI-Nexi\Nexi_DB_AI\docker-lab"
docker compose stop

Write-Host ""
Write-Host "✅ EVERYTHING IS SHUT DOWN." -ForegroundColor Green
Write-Host "   - Web Interface: OFF"
Write-Host "   - Agents:        OFF"
Write-Host "   - Database:      OFF"
Write-Host "   - Docker Lab:    OFF"
