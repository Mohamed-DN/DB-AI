Write-Host "🚀 Waking up Nexi AI Agents..."

# 1. Scout (Auto Discovery)
Write-Host " - Triggering Auto-Discovery..."
try {
    Invoke-RestMethod -Method Post -Uri "http://localhost:8005/api/action/scan" -ErrorAction Stop
    Write-Host "   [OK] Scout started." -ForegroundColor Green
} catch {
    Write-Host "   [FAIL] Scout failed: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 1

# 2. OEM Collector (Oracle Enterprise Manager)
Write-Host " - Triggering OEM Collector..."
try {
    Invoke-RestMethod -Method Post -Uri "http://localhost:8005/api/action/oem-collect" -ErrorAction Stop
    Write-Host "   [OK] OEM Collector started." -ForegroundColor Green
} catch {
    Write-Host "   [FAIL] OEM Collector failed: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 1

# 3. CheckMK Bridge (Legacy Monitoring)
Write-Host " - Triggering CheckMK Sync..."
try {
    Invoke-RestMethod -Method Post -Uri "http://localhost:8005/api/action/checkmk-sync" -ErrorAction Stop
    Write-Host "   [OK] CheckMK Sync started." -ForegroundColor Green
} catch {
    Write-Host "   [FAIL] CheckMK failed: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 1

# 4. Collector (Metric Polling)
Write-Host " - Triggering General Collector..."
try {
    Invoke-RestMethod -Method Post -Uri "http://localhost:8005/api/action/collect" -ErrorAction Stop
    Write-Host "   [OK] Collector started." -ForegroundColor Green
} catch {
    Write-Host "   [FAIL] Collector failed: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 1

# 5. Sentinel (AI Analysis)
Write-Host " - Triggering Sentinel AI..."
try {
    Invoke-RestMethod -Method Post -Uri "http://localhost:8005/api/action/sentinel" -ErrorAction Stop
    Write-Host "   [OK] Sentinel started." -ForegroundColor Green
} catch {
    Write-Host "   [FAIL] Sentinel failed: $_" -ForegroundColor Red
}

Write-Host "✅ All Agents Triggered! Logic should now be active."
