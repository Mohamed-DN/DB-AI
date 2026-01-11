# MongoDB (CMDB)

## Scopo del progetto
MongoDB stores inventory, metrics, alerts, and configuration for the platform.

## Installazione e Setup
Use docker-lab or supply a MongoDB instance. Configure:
MONGODB_HOST, MONGODB_DB, MONGO_USERNAME, MONGO_PASSWORD.
Optional: MONGO_CONTAINER for MongoProxy.

## Architettura
Key collections:
- inventory_databases
- monitoring_alerts
- system_config
- discovery_queue
- business_services
- gateways
- agent_runs
- baselines
- compliance_reports
- rag_knowledge_base

## Utilizzo
Use Mongo Express or mongosh to inspect data.
Example: db.inventory_databases.find({}).limit(5)
