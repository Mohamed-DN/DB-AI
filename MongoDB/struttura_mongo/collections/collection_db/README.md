# Collection: inventory_databases

## Scopo del progetto
Primary CMDB collection representing each database as a digital twin.

## Installazione e Setup
Created by Scout and enriched by Collector. No manual setup.

## Architettura
Key sections:
- identity: db_unique_name, engine, environment, topology, host, gateway_ref
- connection: host, port, service_name, credentials (if stored)
- configuration: version and engine specific config
- state: status, metrics, last_check, last_metric_update
- business_service: ownership metadata

## Utilizzo
Example:
db.inventory_databases.find({ "identity.engine": "POSTGRES" })
db.inventory_databases.updateOne({ "identity.db_unique_name": "DB1" }, { $set: { "state.status": "UP" } })
