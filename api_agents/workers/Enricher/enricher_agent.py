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
    import cx_Oracle
    CX_ORACLE_AVAILABLE = True
except ImportError:
    CX_ORACLE_AVAILABLE = False
    print("[INFO] cx_Oracle not available - Oracle enrichment via oracledb only")


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
                print(f"   ⏭️ Oracle enrichment not yet implemented")
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
