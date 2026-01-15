# =============================================================================
# NEXI AI CMDB - FULL START EVERYTHING
# =============================================================================
# Starts Docker Containers, Backend, and Frontend.
# =============================================================================

Write-Host ""
Write-Host "🚀 STARTING EVERYTHING..." -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = "c:\AI-Nexi\Nexi_DB_AI"

# 1. Start Docker Containers
Write-Host "[1/3] Starting Docker Lab..." -ForegroundColor Yellow
cd "$ProjectRoot\ops\docker-lab"
docker compose up -d

# Write-Host "[2/3] Starting MongoDB Stack..." -ForegroundColor Yellow
# cd "$ProjectRoot\mongo"
# docker compose up -d

# 2. Start Backend
Write-Host "[3/3] Starting Web Interface..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot\api_agents\api_gateway'; Write-Host 'Backend API - Port 8000' -ForegroundColor Green; python main.py"

# 3. Start Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot\web\dashboard'; Write-Host 'React Frontend - Port 3002' -ForegroundColor Green; npm run dev"

Write-Host ""
Write-Host "✅ EVERYTHING STARTED!" -ForegroundColor Green
Write-Host "   Web: http://localhost:3002"
Write-Host "   API: http://localhost:8000"
Write-Host "   DB:  http://localhost:8081"
