Write-Host "🔄 Restarting Backend on Port 8005..."

# 1. Kill existing backend
$port = 8005
$process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($process) {
    Write-Host " - Killing process on port $port..."
    Stop-Process -Id $process.OwningProcess -Force -ErrorAction SilentlyContinue
} else {
    Write-Host " - No process found on port $port."
}

Start-Sleep -Seconds 2

# 2. Start Backend
Write-Host " - Starting Backend..."
$backendScript = "$PSScriptRoot\..\..\api_agents\api_gateway\main.py"
Start-Process -FilePath "python" -ArgumentList "$backendScript" -NoNewWindow

Write-Host "✅ Backend Restarted. Please wait 10 seconds before checking Dashboard."
