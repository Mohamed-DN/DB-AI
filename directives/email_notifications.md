# Email Notifications

## Goal
Send email notifications for critical alerts and system events.

## Inputs
- Alert data (service, host, message, severity)
- Email configuration from .env

## Execution Scripts
- `Agents/CriticalAlert/main.py` - Alert processor with email sending
- `execution/send_alert_email.py` - Standalone email sender (NEW)

## Steps
1. Receive critical alert trigger
2. Format HTML email from template
3. Send via SMTP
4. Save copy to `emails/` directory
5. Mark alert as notified in MongoDB

## Configuration
- Email templates in Agents/CriticalAlert/templates/
- SMTP settings in .env:
  - SMTP_HOST
  - SMTP_PORT
  - SMTP_USER
  - SMTP_PASSWORD
  - EMAIL_FROM
  - EMAIL_TO

## Edge Cases
- SMTP connection failed: log error, retry 3 times
- Rate limiting: queue emails, max 10/minute
- Template missing: use fallback plain text

## Learnings
- Emails stored in emails/ directory with timestamp naming
- 487 email files currently in directory
