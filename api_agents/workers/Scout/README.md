# Scout Agent

## Scopo del progetto
Auto-discovery of databases and containers to populate inventory.

## Installazione e Setup
Requires Docker access and MongoDB. No extra dependencies.

## Architettura
Scans Docker containers and writes to inventory_databases and discovery_queue.

## Utilizzo
python Agents/Scout/main.py --once
