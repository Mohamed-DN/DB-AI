Write-Host "🔥 STARTING DISASTER SCENARIO..."
Write-Host "🔴 Stopping Bratislava DEV..."
docker stop nexi-pg-bratislava-dev
Write-Host "⏳ Waiting 20 seconds..."
Start-Sleep -Seconds 20
Write-Host "🔴 Stopping Milan DEV (Complete Disaster)..."
docker stop nexi-pg-milano-dev
Write-Host "💀 DISASTER COMPLETE."
