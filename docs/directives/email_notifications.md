# Directive: email_notifications

## Goal
Send email notifications for critical alerts and reports.

## Inputs
- **monitoring_alerts**: Alerts with severity CRITICAL
- **SMTP Config**: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
- **ALERT_EMAIL**: Recipient address

## Outputs
- **HTML Email**: Sent to configured recipients
- **emails/**: Local archive of sent emails

## Tools/Scripts
- `Agents/CriticalAlert/main.py`: Main alerting agent (includes email)

## Edge Cases
- **SMTP Failure**: Retry 3 times, then log error
- **Invalid Email**: Validate format before sending
- **Rate Limit**: Max 10 emails per hour to prevent spam

## API
```
GET /api/emails          # List archived emails
GET /api/emails/{file}   # Get email content
DELETE /api/emails/{file}  # Delete email
DELETE /api/emails        # Delete all emails
```

## Usage
```powershell
# Configure in .env
ALERT_EMAIL=dba-team@example.com
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=alerts@example.com
SMTP_PASSWORD=secret

# Run agent
python Agents/CriticalAlert/main.py --once --email dba-team@example.com
```

## Email Format
- Subject: `[CRITICAL ALERT] {db_name} - {message}`
- Body: HTML with alert details, timestamp, suggested actions
