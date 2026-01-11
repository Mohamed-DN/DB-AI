# Collector Agent

## Scopo del progetto
Collect runtime metrics and enrich inventory.

## Installazione e Setup
- pip install -r Agents/Collector/requirements.txt
- Ensure Docker and MongoDB are running

## Architettura
Reads inventory targets, collects docker stats or remote metrics, and updates
inventory_databases.state.metrics.

## Utilizzo
python Agents/Collector/main.py --once
