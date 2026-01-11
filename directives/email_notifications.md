# Directive: email_notifications

## Scopo del progetto
Send alert notifications for critical events.

## Installazione e Setup
Set ALERT_EMAIL or SMTP_USER/SMTP_PASSWORD in the environment.

## Architettura
CriticalAlert checks inventory, writes monitoring_alerts, and sends SMTP mail.

## Utilizzo
POST /api/action/check
Or run: python Agents/CriticalAlert/main.py --once --email you@example.com
