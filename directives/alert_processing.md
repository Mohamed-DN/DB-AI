# Alert Processing

## Goal
Process system alerts from monitoring agents, triage by severity, trigger notifications, and update alert status in MongoDB.

## Inputs
- Alert data from CriticalAlert agent or API
- Alert severity levels: CRITICAL, WARNING, INFO

## Execution Scripts
- `execution/send_alert_email.py` - Send email notification for critical alerts
- `execution/process_alert.py` - Update alert status in MongoDB

## Steps
1. Receive alert from source (agent or API)
2. Check alert severity
3. If CRITICAL: send immediate email notification
4. Store alert in `monitoring_alerts` collection
5. Mark as processed when acknowledged

## Edge Cases
- Email server not available: log error, retry later
- Duplicate alerts: deduplicate by service+host+message within 5 minutes
- MongoDB connection failed: use MongoProxy with container name `nexi-cmdb-mongo`

## Learnings
- MongoDB auth: admin/admin123 on admin database
- Container must be on `docker-lab_nexi-lab` network
