# Metric Collection

## Goal
Collect database metrics (CPU, memory, storage, connections, sessions) from Oracle and PostgreSQL databases.

## Inputs
- Database connection info from `inventory_databases` collection
- Database credentials (AIAUTO user)

## Execution Scripts
- `Agents/Collector/main.py` - Main collector agent
- `Agents/Collector/oracle_collector.py` - Oracle-specific metrics
- `Agents/Collector/postgres_collector.py` - PostgreSQL-specific metrics

## Steps
1. Query MongoDB for active databases (status=UP)
2. For each database, connect using gateway if needed
3. Execute metric queries:
   - Oracle: V$SYSSTAT, V$SESSION, DBA_TABLESPACE_USAGE_METRICS
   - PostgreSQL: pg_stat_activity, pg_stat_database
4. Update `state.metrics` in MongoDB document
5. Log collection timestamp

## Edge Cases
- Connection timeout: mark database as DOWN, log error
- Invalid credentials: log error, do not update metrics
- Gateway required: use maesdn-gateway for Docker Lab databases

## Learnings
- Oracle RAC: CDBRAC_RAC1 (192.168.56.101), CDBRAC_RAC2 (192.168.56.102)
- Gateway hosts: 172.20.3.10 for docker-lab network
- AIAUTO user password: standardized across all DBs
