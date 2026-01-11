# Project Context (v3)

## Scopo del progetto
Nexi DBA AI is an AI assisted CMDB and monitoring stack.

## Installazione e Setup
Use README.md. The root .env drives ports and credentials.

## Architettura
Data layer: MongoDB (CMDB), Qdrant (vectors), Redis (queues), Ollama (LLM).
Control plane: FastAPI backend and agents.
UI: React dashboard.

## Utilizzo
- Inventory: inventory_databases collection.
- Alerts: monitoring_alerts collection.
- Agent intervals: system_config collection.
- Discovery tasks: discovery_queue collection.
