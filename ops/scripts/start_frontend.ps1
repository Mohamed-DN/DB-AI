# Start Frontend UI
$ProjectRoot = "c:\AI-Nexi\Nexi_DB_AI"
Write-Host "🚀 Starting React Frontend (Port 3002)..." -ForegroundColor Green
Set-Location "$ProjectRoot\web\dashboard"
npm run dev
Read-Host "Press Enter to exit..."
