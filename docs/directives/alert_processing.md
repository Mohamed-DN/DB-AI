# Directive: alert_processing

## Goal
Process alerts, enrich with AI analysis, and trigger notifications.

## Inputs
- **monitoring_alerts**: Collection with unprocessed alerts
- **Ollama LLM**: For AI-powered root cause analysis
- **SMTP Config**: For email notifications

## Outputs
- **ai_analysis**: Field added to processed alerts
- **Email**: Sent to ALERT_EMAIL for CRITICAL alerts
- **processed**: Flag set to true

## Tools/Scripts
- `Agents/CriticalAlert/main.py`: Main alerting agent
- `Agents/Watcher/ai_analyzer.py`: Forensic analysis

## Edge Cases
- **LLM Offline**: Skip AI analysis, still send alert
- **SMTP Failure**: Log error, mark alert as requiring manual review
- **Duplicate Alerts**: Check `processed` flag before re-alerting

## API
```
GET /api/alerts          # Get pending alerts
POST /api/action/check   # Trigger check manually
DELETE /api/alerts       # Clear all alerts
```

## Usage
```powershell
# CLI with email
python Agents/CriticalAlert/main.py --once --email dba@example.com

# Or via API
curl -X POST http://localhost:8000/api/action/check
```
