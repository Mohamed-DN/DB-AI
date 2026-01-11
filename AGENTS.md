# Agents Overview

## Scopo del progetto
Describe the agent layer that discovers systems, collects metrics, and produces alerts.

## Installazione e Setup
- Install Python dependencies per agent (see Agents/*/requirements.txt when present).
- Ensure Docker and MongoDB are running.
- Configure ALERT_EMAIL or SMTP_USER/SMTP_PASSWORD for email alerts.

## Architettura
Agents run as independent Python processes and write results to MongoDB:
- Scout: auto discovery of databases and containers.
- Collector: metrics and deep inventory enrichment.
- Watcher: log monitoring and anomaly detection.
- Forensic Analyzer: AI root cause analysis (Watcher companion).
- CriticalAlert: availability checks and alert creation.
- CheckMK Bridge: import external monitoring data.
- DailyAudit: scheduled checks and reports.
- AIAssistant: AI tools for chat (optional).

Intervals are stored in MongoDB system_config keys like scout_interval.

## Utilizzo
Run once from CLI:
- python Agents/Scout/main.py --once
- python Agents/Collector/main.py --once
- python Agents/CriticalAlert/main.py --once --email you@example.com
Or use the Agents panel in the web UI.
