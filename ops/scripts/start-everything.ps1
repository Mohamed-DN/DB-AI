# SIMPLIFIED STARTUP SCRIPT
$ErrorActionPreference = "SilentlyContinue"

Write-Host "1. Killing old processes..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 8000, 3002 | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { 
    Write-Host "   Killing PID $_"
    Stop-Process -Id $_ -Force
}

Write-Host "2. Cleaning duplicates..." -ForegroundColor Yellow
$env:PYTHONPATH = "c:\AI-Nexi\Nexi_DB_AI"
python "c:\AI-Nexi\Nexi_DB_AI\execution\clean_duplicates.py"

Write-Host "3. Installing dependencies..." -ForegroundColor Yellow
pip install -r "c:\AI-Nexi\Nexi_DB_AI\api_agents\api_gateway\requirements.txt"
Set-Location "c:\AI-Nexi\Nexi_DB_AI\web\dashboard"
cmd /c "npm install"

Write-Host "4. Starting Backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-File", "c:\AI-Nexi\Nexi_DB_AI\ops\scripts\start_backend.ps1"

Write-Host "5. Starting Frontend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-File", "c:\AI-Nexi\Nexi_DB_AI\ops\scripts\start_frontend.ps1"

Write-Host "✅ DONE! Check the new windows." -ForegroundColor Cyan
