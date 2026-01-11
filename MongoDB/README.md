# MongoDB (CMDB)

> Central data store for inventory, metrics, alerts, and configuration.

## Connection (V2)

```
Host: localhost
Port: 28017
Database: nexi_cmdb_v2
User: admin
Password: nexi2024
```

## Collections

| Collection | Purpose | Sample Query |
|------------|---------|--------------|
| `inventory_databases` | Discovered DBs | `db.inventory_databases.find()` |
| `monitoring_alerts` | Active alerts | `db.monitoring_alerts.find({processed: false})` |
| `system_config` | Settings | `db.system_config.find({key: "scout_interval"})` |
| `gateways` | SSH gateways | `db.gateways.find()` |
| `business_services` | Service mapping | `db.business_services.find()` |

## Tools

```powershell
# Mongo Express UI
http://localhost:9081

# CLI
docker exec -it nexi-mongodb2 mongosh nexi_cmdb_v2 -u admin -p nexi2024

# Seed collections (if empty)
python execution/seed_mongodb.py
```

## Schema

See `MongoDB/struttura_mongo/collections/` for schema definitions.
