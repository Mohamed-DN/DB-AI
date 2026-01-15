
# Start Scout and CriticalAlert in new windows
Start-Process python -ArgumentList "Agents/Scout/main.py --interval 10" -WindowStyle Minimized
Start-Process python -ArgumentList "Agents/CriticalAlert/critical_alert.py --interval 10" -WindowStyle Minimized
Write-Host "✅ Monitoring Agents Restarted"
