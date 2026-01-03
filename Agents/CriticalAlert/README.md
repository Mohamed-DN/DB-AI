# CriticalAlert Agent

Real-time agent that monitors for critical errors and triggers immediate alerts.

## Schedule
- **Frequency**: Continuous (polling every 30 seconds)
- **Source**: Checkmk + direct DB checks

## Critical Conditions Monitored

| Condition | Severity | Action |
|-----------|----------|--------|
| Database DOWN | CRITICAL | Email BAO + DL |
| Tablespace > 95% | CRITICAL | Email BAO |
| Data Guard LAG > 1 hour | HIGH | Email DL |
| Backup failed | HIGH | Email DL |
| Blocking session > 30 min | MEDIUM | Log + Alert |

## Integration
- Reads from `monitoring_alerts` (Checkmk sync)
- Queries CMDB for contact info
- Sends emails via SMTP
