# CMDB Data Model

## Scopo del progetto
Describe the logical CMDB data model and its collections.

## Installazione e Setup
See MongoDB/README.md.

## Architettura
Collections are grouped by purpose:
- inventory_databases as the core entity
- monitoring_alerts for events
- system_config for agent intervals and global status
- discovery_queue for pending discovery tasks
- business_services and gateways for ownership and routing
- rag_knowledge_base for AI context

## Utilizzo
Use the collection specific docs under struttura_mongo/collections.
