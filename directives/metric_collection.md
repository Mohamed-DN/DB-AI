# Directive: metric_collection

## Scopo del progetto
Trigger metric collection and refresh inventory.

## Installazione e Setup
Collector agent and MongoDB must be available.

## Architettura
- API: POST /api/action/collect
- Runs Agents/Collector/main.py --once
- Writes metrics to inventory_databases.state.metrics

## Utilizzo
POST /api/action/collect
