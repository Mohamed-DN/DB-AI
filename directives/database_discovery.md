# Directive: database_discovery

## Scopo del progetto
Discover databases and populate inventory.

## Installazione e Setup
Scout agent requires Docker access and MongoDB.

## Architettura
- API: POST /api/action/scan
- Runs Agents/Scout/main.py --once
- Writes inventory_databases and discovery_queue

## Utilizzo
POST /api/action/scan
