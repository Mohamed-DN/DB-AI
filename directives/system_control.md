# Directive: system_control

## Scopo del progetto
Control global system state (running or paused).

## Installazione e Setup
No extra setup. Requires MongoDB and the backend service.

## Architettura
- API: POST /api/system/status
- system_config key: global_status
- Agents read global_status and pause when set to PAUSED.

## Utilizzo
Pause:
POST /api/system/status { "status": "PAUSED" }

Resume:
POST /api/system/status { "status": "RUNNING" }
