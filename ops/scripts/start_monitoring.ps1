
# Start Scout and CriticalAlert in new windows
Start-Process python -ArgumentList "api_agents/workers/Scout/main.py --interval 10" -WindowStyle Minimized
Start-Process python -ArgumentList "api_agents/workers/CriticalAlert/critical_alert.py --interval 10" -WindowStyle Minimized
Write-Host "✅ Monitoring Agents Restarted"
