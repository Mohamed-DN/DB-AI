$env:PYTHONPATH = "c:\AI-Nexi\Nexi_DB_AI"
$env:PYTHONIOENCODING = "utf-8"
Write-Host "🚀 Starting Orchestrator..."
Start-Process python -ArgumentList "c:\AI-Nexi\Nexi_DB_AI\Orchestrator\main.py" -RedirectStandardOutput "c:\AI-Nexi\Nexi_DB_AI\orchestrator.log" -RedirectStandardError "c:\AI-Nexi\Nexi_DB_AI\orchestrator_err.log" -PassThru
Write-Host "🚀 Starting CriticalAlert Agent..."
Start-Process python -ArgumentList "c:\AI-Nexi\Nexi_DB_AI\Agents\CriticalAlert\main.py", "--email", "mohamed.d.n.2002@gmail.com", "--interval", "5" -RedirectStandardOutput "c:\AI-Nexi\Nexi_DB_AI\critical_alert.log" -RedirectStandardError "c:\AI-Nexi\Nexi_DB_AI\critical_alert_err.log" -PassThru
Write-Host "✅ Agents running in background. Logs in root folder."
