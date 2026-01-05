$env:PYTHONPATH = "c:\AI-Nexi\Nexi_DB_AI"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "🚀 Launching Nexi AI Stack..."

# 1. Scout Agent (Continuous)
Write-Host "Starting Scout Agent..."
Start-Process -FilePath "python" -ArgumentList "c:\AI-Nexi\Nexi_DB_AI\Agents\Scout\main.py" -WindowStyle Minimized

# 2. Critical Alert Agent (Continuous)
Write-Host "Starting CriticalAlert Agent..."
Start-Process -FilePath "python" -ArgumentList "c:\AI-Nexi\Nexi_DB_AI\Agents\CriticalAlert\main.py" -WindowStyle Hidden

# 3. Collector Agent (Continuous)
Write-Host "Starting Collector Agent (Metrics)..."
Start-Process -FilePath "python" -ArgumentList "c:\AI-Nexi\Nexi_DB_AI\Agents\Collector\main.py" -WindowStyle Hidden

# 4. AI Orchestrator (Continuous)
Write-Host "Starting AI Orchestrator..."
Start-Process -FilePath "python" -ArgumentList "c:\AI-Nexi\Nexi_DB_AI\Orchestrator\main.py" -WindowStyle Minimized

# 5. Web Dashboard (Backend + Frontend)
Write-Host "Starting Dashboard Components..."
Start-Process -FilePath "powershell" -ArgumentList "-ExecutionPolicy Bypass -File c:\AI-Nexi\Nexi_DB_AI\WebInterface\run_dashboard.ps1"

Write-Host "✅ Full Stack Running."
Write-Host "   - 3 Background Agents"
Write-Host "   - 2 Web Services"
