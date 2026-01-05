Write-Host "🚀 Starting Nexi AI Stack (Full System)..." -ForegroundColor Green

# 1. Start Docker
Write-Host "   Starting Docker Containers..."
Set-Location "c:\AI-Nexi\Nexi_DB_AI\docker-lab"
docker-compose up -d

# 2. Wait for DBs?
Write-Host "   Waiting 5s for DBs to initialize..."
Start-Sleep -Seconds 5

# 3. Start Application
Set-Location "c:\AI-Nexi\Nexi_DB_AI"
.\start_full_stack.ps1
