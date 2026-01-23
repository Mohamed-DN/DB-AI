# CriticalAlert Agent

## Scopo del progetto
Monitor database availability and create critical alerts.

## Installazione e Setup
- pip install -r Agents/CriticalAlert/requirements.txt
- Set ALERT_EMAIL or SMTP_USER/SMTP_PASSWORD

## Architettura
- Reads inventory_databases via MongoProxy
- Writes monitoring_alerts
- Sends SMTP or saves HTML files in emails/

## Utilizzo
python Agents/CriticalAlert/main.py --once --email you@example.com
