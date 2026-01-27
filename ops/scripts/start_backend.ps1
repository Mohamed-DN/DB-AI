# Start Backend API
$ProjectRoot = "c:\AI-Nexi\Nexi_DB_AI"
Write-Host "🚀 Starting Backend API (Port 8000)..." -ForegroundColor Green
$env:PYTHONPATH = $ProjectRoot
Set-Location $ProjectRoot
# Use standard python -m to run the module
python -m api_agents.api_gateway.main
Read-Host "Press Enter to exit..."
