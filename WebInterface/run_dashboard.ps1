$env:PYTHONPATH = "c:\AI-Nexi\Nexi_DB_AI"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "🚀 Starting Nexi AI CMDB Dashboard..."

# 1. Start Backend
Write-Host "Backend: Starting FastAPI on port 8000..."
Start-Process -FilePath "python" -ArgumentList "-m uvicorn main:app --host 127.0.0.1 --port 8000 --reload" -WorkingDirectory "c:\AI-Nexi\Nexi_DB_AI\WebInterface\backend" -WindowStyle Minimized

# 2. Start Frontend (Simple HTTP Server)
Write-Host "Frontend: Starting Server on port 3000..."
Start-Process -FilePath "python" -ArgumentList "-m http.server 3000" -WorkingDirectory "c:\AI-Nexi\Nexi_DB_AI\WebInterface\frontend" -WindowStyle Minimized

# 3. Start Agents (Monitoring & Alerts)
Write-Host "Agents: Starting Scout & CriticalAlert..."
Start-Process -FilePath "python" -ArgumentList "Agents\Scout\main.py" -WorkingDirectory "c:\AI-Nexi\Nexi_DB_AI" -WindowStyle Minimized
Start-Process -FilePath "python" -ArgumentList "Agents\CriticalAlert\critical_alert.py" -WorkingDirectory "c:\AI-Nexi\Nexi_DB_AI" -WindowStyle Minimized

# 3. Wait a bit
Start-Sleep -Seconds 5

# 4. Open Browser
Write-Host "🌍 Opening Dashboard..."
Start-Process "http://localhost:3000"

Write-Host "✅ Dashboard is running!"
Write-Host "   Frontend: http://localhost:3000"
Write-Host "   Backend:  http://localhost:8000"
Write-Host "   Note: Ensure MongoDB and Ollama are running in Docker."
