# Directive: metric_collection

## Goal
Collect performance metrics from discovered databases and store in inventory.

## Inputs
- **inventory_databases**: List of databases to query
- **Database Credentials**: AIAUTO user provisioned by Scout

## Outputs
- **state.metrics**: Object with CPU, memory, connections, etc.
- **state.last_metric_update**: Timestamp

## Tools/Scripts
- `Agents/Collector/main.py`: Main collection agent
- `Agents/Collector/pg_collector.py`: PostgreSQL metrics
- `Agents/Collector/oracle_collector.py`: Oracle metrics

## Edge Cases
- **Connection Failure**: Mark DB as DOWN, skip metrics
- **Permission Denied**: Log error, try again next cycle
- **Timeout**: Use 30s timeout per database

## API
```
POST /api/action/collect   # Trigger collection manually
```

## Usage
```powershell
# CLI
python Agents/Collector/main.py --once

# Continuous mode (uses collector_interval from config)
python Agents/Collector/main.py
```

## Metrics Collected

| Engine | Metrics |
|--------|---------|
| PostgreSQL | connections, size, version, uptime |
| Oracle | sessions, tablespace, SGA, PGA |
