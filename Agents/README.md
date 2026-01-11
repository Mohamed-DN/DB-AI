# Agents (Folder)

## Scopo del progetto
Describe the agent executables that run discovery, monitoring, and alerting tasks.

## Installazione e Setup
Install requirements per agent when present. Ensure Docker and MongoDB are running.

## Architettura
- Scout: auto discovery
- Collector: metrics collection
- Watcher: log monitoring
- CriticalAlert: availability checks and notifications
- CheckMK Bridge: external monitoring sync
- DailyAudit: periodic reports

## Utilizzo
Use the Agents panel in the UI or run agents from CLI with --once.
