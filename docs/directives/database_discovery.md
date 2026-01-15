# Directive: database_discovery

## Goal
Discover databases running in Docker and populate the MongoDB inventory.

## Inputs
- **Docker Access**: Requires Docker CLI access to list containers
- **GATEWAY_SUFFIX**: Environment variable ("2" for V2, empty for V1)

## Outputs
- **inventory_databases**: Collection populated with discovered DBs
- **monitoring_alerts**: NEW_DB_DISCOVERED alerts for new databases
- **AIAUTO User**: Provisioned on each new database

## Tools/Scripts
- `Agents/Scout/main.py`: Main discovery agent
- `execution/discover_docker_databases.py`: Standalone discovery script

## Edge Cases
- **Gateway Missing**: DB is skipped if its gateway container is not running
- **Port Parsing Failure**: Defaults to engine default (5432 for PG, 1521 for Oracle)
- **Duplicate Detection**: Uses `db_unique_name` for deduplication

## API
```
POST /api/action/scan
POST /api/auto-discovery
```

## Usage
```powershell
# CLI
python Agents/Scout/main.py --once

# Or via API
curl -X POST http://localhost:9000/api/auto-discovery
```
