# Directive: container_monitoring

## Goal
Monitor container logs for anomalies and errors.

## Inputs
- **Docker Logs**: `docker logs` output from database containers
- **Patterns**: Error patterns to detect (ORA-, FATAL, etc.)

## Outputs
- **monitoring_alerts**: Alerts for detected anomalies
- **log_events**: Collection with log snippets

## Tools/Scripts
- `Agents/Watcher/main.py`: Log monitoring agent
- `Agents/Watcher/ai_analyzer.py`: AI-powered log analysis

## Edge Cases
- **Log Rotation**: Track last position to avoid duplicates
- **High Volume**: Rate limit to max 100 events per minute
- **Container Restart**: Detect and create alert

## API
```
# No direct API - runs as background agent
```

## Usage
```powershell
# CLI
python Agents/Watcher/main.py --once

# Continuous mode
python Agents/Watcher/main.py
```

## Patterns Detected

| Engine | Patterns |
|--------|----------|
| Oracle | ORA-\d{5}, TNS-\d{5} |
| PostgreSQL | FATAL, ERROR, PANIC |
| Generic | OutOfMemory, Segmentation fault |
