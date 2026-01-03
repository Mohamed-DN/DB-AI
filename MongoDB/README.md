# CMDB Structure (AI-Driven)

The CMDB is designed to be populated automatically by SADA agents. It follows a "Business Service -> Database -> Gateway" model.

## Collections Structure

1. **Inventory Databases** (`CMDB_Inventory`)
   - Digital twin of each database.
   - Contains: Identity, Topology, Physical Architecture, Config, Licensing, Data Protection, Storage.

2. **Gateways**
   - Access infrastructure (Bastion/Jump hosts).
   - Links to reachable databases.

3. **Business Services**
   - Links technical resources to business value.
   - Contacts, ServiceNow IDs.

## Directory Contents

- **Schemas/**: Schema definitions and metadata mapping documentation (formerly `MongodDB`).
- **struttura_mongo/**: Logical linking and collection organization.
- **Script_oracle_to_mongo.sql**: Legacy/Reference script for migration logic.
