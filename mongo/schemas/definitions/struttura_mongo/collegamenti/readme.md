# Collection Relationships

## Scopo del progetto
Describe relationships between CMDB collections.

## Installazione e Setup
See MongoDB/README.md.

## Architettura
inventory_databases links to:
- gateways via identity.gateway_ref
- business_services via business_service
- monitoring_alerts via db_unique_name
Other collections reference inventory_databases by db_unique_name.

## Utilizzo
Use these relationships when building reports or join-like queries in the UI.
