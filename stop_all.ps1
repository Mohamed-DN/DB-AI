Write-Host "🛑 Stopping Nexi AI Stack..." -ForegroundColor Red

# 1. Stop Python Agents
Write-Host "   Killing Python Agents..."
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "uvicorn" -Force -ErrorAction SilentlyContinue

# 2. Stop Docker Environment
Write-Host "   Stopping Docker Containers..."
Set-Location "c:\AI-Nexi\Nexi_DB_AI\docker-lab"
docker-compose stop

Write-Host "✅ System Stopped. (All Python processes and Docker containers halted)"
