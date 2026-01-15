"""
Enricher Agent - Updates existing MongoDB documents with LIVE data from database connections.
Connects to PostgreSQL, Oracle, and other databases to collect real-time metadata.
"""
import os
import sys
import time
import argparse
from datetime import datetime
from typing import Dict, Any, Optional, List

# Force UTF-8 for Windows Console
sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from orchestrator.core.mongo_proxy import MongoProxy

# Optional imports for database connections
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("[WARN] psycopg2 not available - PostgreSQL enrichment disabled")

try:
    import oracledb
    oracledb.init_oracle_client()  # Try to initialize Oracle Instant Client
    ORACLEDB_AVAILABLE = True
except ImportError:
    ORACLEDB_AVAILABLE = False
    print("[INFO] oracledb not available - Oracle enrichment disabled")
except Exception as e:
    ORACLEDB_AVAILABLE = True  # Module available but Instant Client may not be
    print(f"[INFO] oracledb available (thin mode): {e}")


class OracleEnricher:
    """Enriches Oracle database documents with live CDB/PDB data"""
    
    def __init__(self, host: str, port: int, service_name: str, user: str, password: str):
        self.host = host
        self.port = port
        self.service_name = service_name
        self.user = user
        self.password = password
    
    def collect(self) -> Optional[Dict[str, Any]]:
        """Connect to Oracle and collect CDB/PDB metadata"""
        if not ORACLEDB_AVAILABLE:
            print("   ⚠️ oracledb not available")
            return None
        
        try:
            # Use thin mode (no Oracle client needed)
            dsn = f"{self.host}:{self.port}/{self.service_name}"
            conn = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=dsn,
                mode=oracledb.DEFAULT_AUTH
            )
            cursor = conn.cursor()
            
            data = {}
            
            # 1. Database Identity
            cursor.execute("""
                SELECT DBID, NAME, DB_UNIQUE_NAME, PLATFORM_NAME, 
                       LOG_MODE, FORCE_LOGGING, FLASHBACK_ON
                FROM V$DATABASE
            """)
            row = cursor.fetchone()
            if row:
                data["dbid"] = row[0]
                data["db_name"] = row[1]
                data["db_unique_name"] = row[2]
                data["platform"] = row[3]
                data["log_mode"] = row[4]
                data["force_logging"] = row[5] == "YES"
                data["flashback_on"] = row[6] == "YES"
            
            # 2. Instance Info
            cursor.execute("""
                SELECT INSTANCE_NAME, INSTANCE_NUMBER, STATUS, 
                       STARTUP_TIME, VERSION_FULL
                FROM V$INSTANCE
            """)
            row = cursor.fetchone()
            if row:
                data["instance_name"] = row[0]
                data["instance_number"] = row[1]
                data["status"] = row[2]
                data["startup_time"] = row[3].isoformat() if row[3] else None
                data["version_full"] = row[4]
            
            # 3. Version Banner
            cursor.execute("SELECT BANNER_FULL FROM V$VERSION WHERE ROWNUM = 1")
            row = cursor.fetchone()
            if row:
                data["banner"] = row[0]
            
            # 4. Check if CDB
            cursor.execute("SELECT CDB FROM V$DATABASE")
            row = cursor.fetchone()
            is_cdb = row and row[0] == "YES"
            data["is_cdb"] = is_cdb
            data["configuration_type"] = "CDB" if is_cdb else "NON-CDB"
            
            # 5. PDB Information (only for CDB)
            pdbs = []
            if is_cdb:
                cursor.execute("""
                    SELECT p.PDB_ID, p.PDB_NAME, p.CON_ID, p.STATUS, p.OPEN_MODE,
                           p.RESTRICTED, p.CREATION_TIME,
                           ROUND(SUM(d.BYTES)/1024/1024/1024, 2) as SIZE_GB
                    FROM V$PDBS p
                    LEFT JOIN CDB_DATA_FILES d ON p.CON_ID = d.CON_ID
                    WHERE p.PDB_NAME != 'PDB$SEED'
                    GROUP BY p.PDB_ID, p.PDB_NAME, p.CON_ID, p.STATUS, 
                             p.OPEN_MODE, p.RESTRICTED, p.CREATION_TIME
                """)
                for row in cursor.fetchall():
                    pdb = {
                        "pdb_id": row[0],
                        "pdb_name": row[1],
                        "con_id": row[2],
                        "status": row[3],
                        "open_mode": row[4],
                        "restricted": row[5] == "YES",
                        "creation_time": row[6].isoformat() if row[6] else None,
                        "total_size_gb": float(row[7]) if row[7] else 0,
                        "tablespaces": [],
                        "services": []
                    }
                    
                    # Get tablespaces for this PDB
                    try:
                        cursor.execute(f"""
                            SELECT TABLESPACE_NAME, 
                                   ROUND(SUM(BYTES)/1024/1024, 2) as SIZE_MB,
                                   STATUS
                            FROM CDB_DATA_FILES 
                            WHERE CON_ID = {row[2]}
                            GROUP BY TABLESPACE_NAME, STATUS
                        """)
                        for ts_row in cursor.fetchall():
                            pdb["tablespaces"].append({
                                "name": ts_row[0],
                                "size_mb": float(ts_row[1]) if ts_row[1] else 0,
                                "status": ts_row[2] or "ONLINE"
                            })
                    except:
                        pass
                    
                    # Get services for this PDB
                    try:
                        cursor.execute(f"""
                            SELECT NAME, NETWORK_NAME, ENABLED
                            FROM CDB_SERVICES 
                            WHERE CON_ID = {row[2]}
                        """)
                        for svc_row in cursor.fetchall():
                            pdb["services"].append({
                                "service_name": svc_row[0],
                                "network_name": svc_row[1],
                                "enabled": svc_row[2] == "YES"
                            })
                    except:
                        pass
                    
                    pdbs.append(pdb)
            
            data["pluggable_databases"] = pdbs
            data["pdb_count"] = len(pdbs)
            
            # 6. SGA/PGA Info
            try:
                cursor.execute("SELECT NAME, VALUE FROM V$SGA WHERE NAME IN ('Fixed Size', 'Variable Size', 'Database Buffers')")
                sga_info = {}
                for row in cursor.fetchall():
                    sga_info[row[0]] = int(row[1])
                data["sga_info"] = sga_info
            except:
                pass
            
            # 7. Session Info
            try:
                cursor.execute("SELECT COUNT(*) FROM V$SESSION WHERE STATUS = 'ACTIVE'")
                data["active_sessions"] = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM V$SESSION")
                data["total_sessions"] = cursor.fetchone()[0]
            except:
                pass
            
            # 8. Data Guard Status
            try:
                cursor.execute("SELECT DATABASE_ROLE, PROTECTION_MODE FROM V$DATABASE")
                row = cursor.fetchone()
                if row:
                    data["dataguard_role"] = row[0]
                    data["protection_mode"] = row[1]
            except:
                pass
            
            # 9. ASM Diskgroups
            try:
                cursor.execute("""
                    SELECT NAME, TOTAL_MB, FREE_MB, STATE, TYPE, REDUNDANCY
                    FROM V$ASM_DISKGROUP
                """)
                asm_diskgroups = []
                for dg in cursor.fetchall():
                    asm_diskgroups.append({
                        "name": dg[0],
                        "total_gb": round(dg[1] / 1024, 2) if dg[1] else 0,
                        "free_gb": round(dg[2] / 1024, 2) if dg[2] else 0,
                        "state": dg[3],
                        "type": dg[4],
                        "redundancy": dg[5]
                    })
                data["asm_diskgroups"] = asm_diskgroups
            except:
                pass  # ASM not accessible from DB instance
            
            # 10. RAC Instances (GV$ views)
            try:
                cursor.execute("""
                    SELECT INST_ID, INSTANCE_NAME, HOST_NAME, STATUS, 
                           LOGINS, ACTIVE_STATE
                    FROM GV$INSTANCE
                    ORDER BY INST_ID
                """)
                rac_instances = []
                for inst in cursor.fetchall():
                    rac_instances.append({
                        "inst_id": inst[0],
                        "instance_name": inst[1],
                        "host_name": inst[2],
                        "status": inst[3],
                        "logins": inst[4],
                        "active_state": inst[5]
                    })
                data["rac_instances"] = rac_instances
                data["is_rac"] = len(rac_instances) > 1
            except:
                data["is_rac"] = False
            
            # 11. VIP and SCAN info (from listener config)
            try:
                cursor.execute("""
                    SELECT INST_ID, NETWORK_NUMBER, NAME, IP_ADDRESS 
                    FROM GV$LISTENER_NETWORK
                """)
                network_info = []
                for row in cursor.fetchall():
                    network_info.append({
                        "inst_id": row[0],
                        "network": row[1],
                        "name": row[2],
                        "ip_address": row[3]
                    })
                data["listener_networks"] = network_info
            except:
                pass
            
            conn.close()
            return data
            
        except Exception as e:
            print(f"   ❌ Oracle connection error: {e}")
            return None


class PostgresEnricher:
    """Enriches PostgreSQL database documents with live data"""
    
    def __init__(self, host: str, port: int, user: str, password: str, database: str = "postgres"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
    
    def collect(self) -> Optional[Dict[str, Any]]:
        """Connect to PostgreSQL and collect metadata"""
        if not PSYCOPG2_AVAILABLE:
            return None
        
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                connect_timeout=10
            )
            cursor = conn.cursor()
            
            data = {}
            
            # 1. Cluster Identity
            cursor.execute("SELECT system_identifier FROM pg_control_system();")
            row = cursor.fetchone()
            data["system_identifier"] = str(row[0]) if row else None
            
            cursor.execute("SELECT timeline_id FROM pg_control_checkpoint();")
            row = cursor.fetchone()
            data["timeline_id"] = row[0] if row else None
            
            cursor.execute("SELECT version();")
            data["version_full"] = cursor.fetchone()[0]
            
            # 2. Instance Details
            cursor.execute("SELECT pg_is_in_recovery();")
            data["is_in_recovery"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT inet_server_addr(), inet_server_port();")
            row = cursor.fetchone()
            data["inet_server_addr"] = str(row[0]) if row[0] else self.host
            data["inet_server_port"] = row[1] if row[1] else self.port
            
            # 3. Resource Config
            cursor.execute("SHOW max_connections;")
            data["max_connections"] = int(cursor.fetchone()[0])
            
            cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active';")
            data["current_active"] = cursor.fetchone()[0]
            
            cursor.execute("SHOW shared_buffers;")
            data["shared_buffers"] = cursor.fetchone()[0]
            
            cursor.execute("SHOW effective_cache_size;")
            data["effective_cache_size"] = cursor.fetchone()[0]
            
            cursor.execute("SHOW wal_level;")
            data["wal_level"] = cursor.fetchone()[0]
            
            # 4. Replication Slots
            cursor.execute("""
                SELECT slot_name, plugin, active, restart_lsn, 
                       pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) as lag_bytes
                FROM pg_replication_slots;
            """)
            slots = []
            for row in cursor.fetchall():
                slots.append({
                    "slot_name": row[0],
                    "plugin": row[1] or "physical",
                    "active": row[2],
                    "restart_lsn": str(row[3]) if row[3] else None,
                    "lag_bytes": int(row[4]) if row[4] else 0
                })
            data["replication_slots"] = slots
            
            # 5. Extensions
            cursor.execute("SELECT extname, extversion FROM pg_extension WHERE extname != 'plpgsql';")
            extensions = []
            for row in cursor.fetchall():
                extensions.append({"name": row[0], "version": row[1]})
            data["extensions_installed"] = extensions
            
            # 6. Storage
            cursor.execute("SELECT pg_database_size(current_database());")
            data["database_size_bytes"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT spcname, pg_tablespace_location(oid) FROM pg_tablespace WHERE spcname NOT IN ('pg_default', 'pg_global');")
            tablespaces = []
            for row in cursor.fetchall():
                tablespaces.append({"name": row[0], "path": row[1]})
            data["tablespaces"] = tablespaces
            
            conn.close()
            return data
            
        except Exception as e:
            print(f"   ❌ PostgreSQL connection error: {e}")
            return None


class EnricherAgent:
    """Main Enricher Agent - updates existing MongoDB documents with live data"""
    
    def __init__(self):
        self.mongo = MongoProxy()
        self.default_pg_user = os.getenv("POSTGRES_USER", "postgres")
        self.default_pg_password = os.getenv("POSTGRES_PASSWORD", "nexi2024")
        print("✅ EnricherAgent initialized")
    
    def get_inventory(self) -> List[Dict]:
        """Get all databases from inventory"""
        try:
            dbs = self.mongo.execute_eval("db.inventory_databases.find({}).toArray()")
            return dbs or []
        except Exception as e:
            print(f"❌ Error fetching inventory: {e}")
            return []
    
    def enrich_postgres(self, db_doc: Dict) -> bool:
        """Enrich a PostgreSQL document with live data"""
        identity = db_doc.get("identity", {})
        connection = db_doc.get("connection", {})
        
        name = identity.get("db_unique_name", "UNKNOWN")
        host = identity.get("host", "127.0.0.1")
        port = connection.get("port", 5432)
        
        print(f"   🔌 Connecting to PostgreSQL: {host}:{port}...")
        
        enricher = PostgresEnricher(
            host=host,
            port=port,
            user=self.default_pg_user,
            password=self.default_pg_password
        )
        
        data = enricher.collect()
        if not data:
            print(f"   ⚠️ Could not collect data from {name}")
            return False
        
        # Build update document
        update_fields = {
            "cluster_identity.system_identifier": data.get("system_identifier"),
            "cluster_identity.timeline_id": data.get("timeline_id"),
            "cluster_identity.version_full": data.get("version_full"),
            "instance_details.is_in_recovery": data.get("is_in_recovery"),
            "instance_details.inet_server_addr": data.get("inet_server_addr"),
            "resource_config.connections.max_connections": data.get("max_connections"),
            "resource_config.connections.current_active": data.get("current_active"),
            "resource_config.memory.shared_buffers": data.get("shared_buffers"),
            "resource_config.memory.effective_cache_size": data.get("effective_cache_size"),
            "resource_config.wal.wal_level": data.get("wal_level"),
            "replication_ha.replication_slots": data.get("replication_slots", []),
            "extensions_installed": data.get("extensions_installed", []),
            "storage_info.database_size_bytes": data.get("database_size_bytes"),
            "storage_info.tablespaces": data.get("tablespaces", []),
            "state.status": "UP",
            "state.last_seen": datetime.now().isoformat(),
            "metadata.last_enriched": datetime.now().isoformat()
        }
        
        # Execute update
        try:
            # Build $set object - filter out None values
            set_obj = {k: v for k, v in update_fields.items() if v is not None}
            
            import json
            set_json = json.dumps(set_obj, default=str)
            
            js_cmd = f"""
            db.inventory_databases.updateOne(
                {{ "identity.db_unique_name": "{name}" }},
                {{ $set: {set_json} }}
            )
            """
            self.mongo.execute_eval(js_cmd)
            print(f"   ✅ Enriched {name} with {len(set_obj)} fields")
            return True
        except Exception as e:
            print(f"   ❌ Update error for {name}: {e}")
            return False
    
    def enrich_oracle(self, db_doc: Dict) -> bool:
        """Enrich an Oracle document with live CDB/PDB data"""
        identity = db_doc.get("identity", {})
        connection = db_doc.get("connection", {})
        
        name = identity.get("db_unique_name", "UNKNOWN")
        host = identity.get("host", "127.0.0.1")
        port = connection.get("port", 1521)
        service_name = connection.get("service_name", "ORCL")
        
        print(f"   🔌 Connecting to Oracle: {host}:{port}/{service_name}...")
        
        # Get Oracle credentials
        oracle_user = os.getenv("ORACLE_USER", "system")
        oracle_password = os.getenv("ORACLE_PASSWORD", "oracle")
        
        enricher = OracleEnricher(
            host=host,
            port=port,
            service_name=service_name,
            user=oracle_user,
            password=oracle_password
        )
        
        data = enricher.collect()
        if not data:
            print(f"   ⚠️ Could not collect data from {name}")
            return False
        
        # Build update document with CDB/PDB structure
        update_fields = {
            "database_core.identity.dbid": data.get("dbid"),
            "database_core.identity.db_name": data.get("db_name"),
            "database_core.identity.instance_name": data.get("instance_name"),
            "database_core.identity.instance_number": data.get("instance_number"),
            "database_core.version_info.full_version": data.get("version_full"),
            "database_core.version_info.banner": data.get("banner"),
            "database_core.startup_time": data.get("startup_time"),
            "database_core.configuration.type": data.get("configuration_type"),
            "database_core.configuration.log_mode": data.get("log_mode"),
            "database_core.configuration.force_logging": data.get("force_logging"),
            "database_core.configuration.flashback_on": data.get("flashback_on"),
            "database_core.configuration.platform": data.get("platform"),
            "pluggable_databases": data.get("pluggable_databases", []),
            "pdb_count": data.get("pdb_count", 0),
            "performance.active_sessions": data.get("active_sessions"),
            "performance.total_sessions": data.get("total_sessions"),
            "ha_dr.dataguard.role": data.get("dataguard_role"),
            "ha_dr.dataguard.protection_mode": data.get("protection_mode"),
            "state.status": "UP",
            "state.last_seen": datetime.now().isoformat(),
            "metadata.last_enriched": datetime.now().isoformat()
        }
        
        # Execute update
        try:
            import json
            set_obj = {k: v for k, v in update_fields.items() if v is not None}
            set_json = json.dumps(set_obj, default=str)
            
            js_cmd = f"""
            db.inventory_databases.updateOne(
                {{ "identity.db_unique_name": "{name}" }},
                {{ $set: {set_json} }}
            )
            """
            self.mongo.execute_eval(js_cmd)
            pdb_count = data.get("pdb_count", 0)
            print(f"   ✅ Enriched {name} with {len(set_obj)} fields, {pdb_count} PDBs")
            return True
        except Exception as e:
            print(f"   ❌ Update error for {name}: {e}")
            return False
    
    def run_once(self):
        """Run one enrichment cycle"""
        print(f"\n{'='*60}")
        print(f"📊 Enricher Agent - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        inventory = self.get_inventory()
        print(f"📋 Found {len(inventory)} databases in inventory")
        
        enriched_count = 0
        for db in inventory:
            identity = db.get("identity", {})
            engine = identity.get("engine", "").upper()
            name = identity.get("db_unique_name", "UNKNOWN")
            
            print(f"\n🔍 Processing: {name} ({engine})")
            
            if engine in ["POSTGRES", "POSTGRESQL"]:
                if self.enrich_postgres(db):
                    enriched_count += 1
            elif engine == "ORACLE":
                if self.enrich_oracle(db):
                    enriched_count += 1
            else:
                print(f"   ⏭️ Skipping {engine} (no enricher available)")
        
        print(f"\n✅ Enrichment complete. Updated {enriched_count}/{len(inventory)} databases.")
    
    def get_interval(self, default: int = 300) -> int:
        """Get enrichment interval from config"""
        try:
            doc = self.mongo.execute_eval("db.system_config.findOne({key: 'enricher_interval'})")
            if doc and 'value' in doc:
                return int(doc['value'])
        except:
            pass
        return default
    
    def check_pause(self) -> bool:
        """Check if system is paused"""
        try:
            doc = self.mongo.execute_eval("db.system_config.findOne({key: 'global_status'})")
            return doc and doc.get('value') == 'PAUSED'
        except:
            return False
    
    def run_continuous(self, interval: int = 300):
        """Run continuous enrichment"""
        print("🔄 Enricher Agent starting continuous mode...")
        while True:
            try:
                if self.check_pause():
                    print("⏸️ System paused. Sleeping...")
                    time.sleep(10)
                    continue
                
                self.run_once()
                actual_interval = self.get_interval(interval)
                print(f"💤 Sleeping for {actual_interval}s...")
                time.sleep(actual_interval)
            except KeyboardInterrupt:
                print("\n🛑 Agent stopped.")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description="Enricher Agent - Updates MongoDB with live DB data")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=300, help="Enrichment interval (seconds)")
    args = parser.parse_args()
    
    agent = EnricherAgent()
    
    if args.once:
        agent.run_once()
    else:
        agent.run_continuous(args.interval)


if __name__ == "__main__":
    main()
