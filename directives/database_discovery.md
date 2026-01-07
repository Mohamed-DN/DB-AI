# Database Discovery Directive

## Goal
Discover all Docker databases and VirtualBox Oracle instances, register them in MongoDB.

## Inputs
- Docker socket (local)
- VirtualBox Oracle IPs (192.168.56.101, 192.168.56.102 for RAC)
- MongoDB connection (nexi-cmdb-mongo, admin/admin123)

## Execution Scripts
- `execution/discover_docker_databases.py` - Scan Docker containers for PostgreSQL/Oracle
- `execution/discover_vbox_databases.py` - Connect to VirtualBox Oracle instances
- `execution/register_database.py` - Insert/update database record in MongoDB

## Steps
1. Run `discover_docker_databases.py` → outputs JSON list of found databases
2. Run `discover_vbox_databases.py` → outputs JSON list of VB Oracle instances
3. For each database, call `register_database.py` with the JSON payload

## Edge Cases
- Container not responding → mark status as DOWN
- VBox SSH timeout → skip but log warning
- Duplicate database → update existing record (upsert)

## Learned
- MongoProxy uses container `nexi-cmdb-mongo` (not nexi-mongodb)
- Credentials: admin/admin123
- Collections: inventory_databases, monitoring_alerts
