import json
import subprocess
import logging

class PostgresExtractor:
    def __init__(self):
        pass

    def _exec_query(self, container: str, db_name: str, sql: str):
        """Execute a SQL query inside the container and return JSON"""
        try:
            # Construct command: psql -> json output
            # We use row_to_json to get clean JSON from valid SQL
            wrapped_sql = f"SELECT row_to_json(t) FROM ({sql}) t"
            
            cmd = [
                "docker", "exec", container,
                "psql", "-U", "postgres", "-d", db_name,
                "-t", # Tuple only (no header)
                "-A", # Unaligned
                "-c", wrapped_sql
            ]
            
            output = subprocess.check_output(cmd).decode('utf-8').strip()
            results = []
            for line in output.split('\n'):
                if line.strip():
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass # Skip connection warnings etc
            
            return results
        except Exception as e:
            # print(f"⚠️ Query Error on {container}: {e}") # Verbose
            return []

    def extract(self, container: str, host: str, port: int, db_unique_name: str):
        """Deep extract for PostgreSQL"""
        print(f"🐘 Deep Extraction for {container}...")
        
        # 1. Identity & Version
        # We assume the DB name for connection is 'postgres' to query system stats, 
        # but for business data we might need the specific DB. 
        # System views are effectively global or available from 'postgres' DB for the instance.
        target_db = "postgres" 

        version_res = self._exec_query(container, target_db, "SELECT version()")
        version = version_res[0]['version'] if version_res else "Unknown"

        # 2. Instance Details (Connections, Archiver)
        instance_q = """
        SELECT 
            (SELECT setting FROM pg_settings WHERE name = 'max_connections')::int as max_connections,
            (SELECT count(*) FROM pg_stat_activity) as active_connections,
            (SELECT pg_is_in_recovery()) as is_in_recovery,
            (SELECT pg_postmaster_start_time()) as start_time
        """
        instance_res = self._exec_query(container, target_db, instance_q)
        inst_data = instance_res[0] if instance_res else {}
        
        archiver_q = "SELECT archived_count, last_archived_wal, last_archived_time, failed_count, last_failed_time FROM pg_stat_archiver"
        archiver_res = self._exec_query(container, target_db, archiver_q)
        
        # 3. Deep Configuration (Memory, WAL, Vacuum)
        config_q = """
        SELECT name, setting 
        FROM pg_settings 
        WHERE name IN ('shared_buffers', 'work_mem', 'maintenance_work_mem', 'effective_cache_size', 'wal_level', 'max_wal_size', 'min_wal_size', 'checkpoint_timeout', 'autovacuum', 'autovacuum_max_workers')
        """
        config_res = self._exec_query(container, target_db, config_q)
        config_map = {row['name']: row['setting'] for row in config_res}

        # 4. Replication (Slots & Peers)
        slots_q = """
        SELECT slot_name, plugin, slot_type, active, restart_lsn, 
               pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) as calculated_lag_bytes 
        FROM pg_replication_slots
        """
        slots_res = self._exec_query(container, target_db, slots_q)
        
        peers_q = """
        SELECT client_addr, state, sync_state, application_name, 
               sent_lsn, write_lsn, flush_lsn, replay_lsn,
               write_lag, flush_lag, replay_lag 
        FROM pg_stat_replication
        """
        peers_res = self._exec_query(container, target_db, peers_q)

        # 5. Storage (Tablespaces & Bloat)
        # Note: pg_database_size needs to be run for the specific business DB, 
        # but we might be connected to postgres. Let's try to list all DB sizes?
        # For this demo, we'll focus on the 'current' database size if we knew the business DB name.
        # But 'postgres' DB is small. Let's sum all DBs?
        db_size_q = "SELECT sum(pg_database_size(datname)) as total_bytes FROM pg_database"
        size_res = self._exec_query(container, target_db, db_size_q)
        total_size = size_res[0]['total_bytes'] if size_res else 0

        tbs_q = """
        SELECT t.spcname, pg_tablespace_location(t.oid) as path, 
               pg_tablespace_size(t.oid) as size_bytes
        FROM pg_tablespace t
        """
        tbs_res = self._exec_query(container, target_db, tbs_q)

        # Build Deep JSON
        deep_metadata = {
            "metadata_version": "2.1-auto",
            "extraction_timestamp": "NOW",
            "cluster_identity": {
                "cluster_name": db_unique_name,
                "version": version,
                "is_in_recovery": inst_data.get('is_in_recovery', False)
            },
            "instance_details": {
                "role": "STANDBY" if inst_data.get('is_in_recovery') else "LEADER",
                "state": "running",
                "uptime_seconds": 0, # TODO: Calc from start_time
                "connections": {
                    "max": inst_data.get('max_connections'),
                    "active": inst_data.get('active_connections')
                },
                "archiver": archiver_res[0] if archiver_res else {}
            },
            "deep_configuration": {
                "memory": {
                    "shared_buffers": config_map.get('shared_buffers'),
                    "work_mem": config_map.get('work_mem'),
                    "maintenance_work_mem": config_map.get('maintenance_work_mem'),
                    "effective_cache_size": config_map.get('effective_cache_size')
                },
                "wal_tuning": {
                    "wal_level": config_map.get('wal_level'),
                    "max_wal_size": config_map.get('max_wal_size'),
                    "min_wal_size": config_map.get('min_wal_size'),
                    "checkpoint_timeout": config_map.get('checkpoint_timeout')
                },
                "autovacuum": {
                    "autovacuum": config_map.get('autovacuum'),
                    "autovacuum_max_workers": config_map.get('autovacuum_max_workers')
                }
            },
            "replication": {
                "sync_standby_names": config_map.get('synchronous_standby_names', ''),
                "replication_slots": slots_res,
                "peers": peers_res
            },
            "storage_deep_dive": {
                "database_size_bytes": total_size,
                "tablespaces": tbs_res
            }
        }
        
        return deep_metadata
