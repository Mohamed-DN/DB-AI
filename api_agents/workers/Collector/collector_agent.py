"""
SADA Collector Agent - Docker & VirtualBox Edition
Collects deep metrics (CPU, RAM, IO) from Docker containers
AND supports Remote Oracle Databases (VirtualBox/External)
"""
import sys
import os
import time
import json
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Force UTF-8 for Windows Console
sys.stdout.reconfigure(encoding='utf-8')

# Load MongoDB Environment Variables
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../.env.v2'))
load_dotenv(env_path)
print(f"DEBUG: MONGO_URI Loaded: {os.getenv('MONGO_URI')}")

# Add source path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Link to Shared Modules (ROOT)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from orchestrator.core.mongo_proxy import MongoProxy

# Local Imports
try:
    from src.extractors import RemoteOracleExtractor
    from src.cmdb_updater import CMDBUpdater
except ImportError:
    # Handle running from root or subfolder
    sys.path.append(os.path.dirname(__file__))
    from src.extractors import RemoteOracleExtractor
    from src.cmdb_updater import CMDBUpdater

class CollectorAgent:
    def __init__(self):
        self.mongo = MongoProxy()
        # Initialize CMDB Updater (uses direct PyMongo)
        try:
            self.cmdb_updater = CMDBUpdater(self.mongo)
            print("✅ CMDB Updater initialized")
        except Exception as e:
            print(f"⚠️ CMDB Updater failed (will skip deep updates): {e}")
            self.cmdb_updater = None
        
    def is_container_running(self, container_name):
        """Check if container is strictly running (docker stats returns 0.00% for stopped containers on Windows)"""
        try:
            cmd = ["docker", "inspect", "-f", "{{.State.Running}}", container_name]
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode('utf-8').strip()
            return output == 'true'
        except:
            return False

    def collect_docker_metrics(self, container_name):
        """Collect real-time metrics from Docker"""
        try:
            # Stats command
            cmd = ["docker", "stats", container_name, "--no-stream", "--format", "{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}|{{.NetIO}}|{{.BlockIO}}"]
            output = subprocess.check_output(cmd).decode('utf-8').strip()
            
            if not output: return None
            
            # Docker might return multiple lines if ambiguous, but usually one.
            lines = output.split('\n')
            parts = lines[0].split('|')
            
            return {
                "cpu_usage": parts[0],      # e.g. "0.05%"
                "ram_usage": parts[1],      # e.g. "50MiB / 1GiB"
                "ram_percent": parts[2],    # e.g. "5.00%"
                "net_io": parts[3],         # e.g. "1kB / 2kB"
                "disk_io": parts[4],        # e.g. "0B / 0B"
                "captured_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            # Container might be down
            return None

    def collect_remote_oracle(self, db_doc):
        """Collect deep metrics from Remote Oracle"""
        if not self.cmdb_updater: return
        
        identity = db_doc.get('identity', {})
        conn = db_doc.get('connection', {})
        
        host = conn.get('host')
        port = conn.get('port', 1521)
        service = conn.get('service_name') or identity.get('db_unique_name')
        user = conn.get('user')
        password = conn.get('password')
        
        if not (host and user and password):
            print(f"   ⚠️ Missing connection details for {identity.get('db_unique_name')}")
            return

        print(f"   🔌 Connecting to Remote Oracle: {host}:{port}/{service}...")
        try:
            extractor = RemoteOracleExtractor(host, port, service, user, password)
            data = extractor.collect_all()
            
            if data:
                # Transform and Upsert
                # Mock system data as we don't have SSH to VBox host yet
                system_data = {
                    "hostname": host,
                    "os": {"name": "VirtualBox/Remote"},
                    "cpu": {"cores": "Unknown"},
                    "memory": {"total_gb": 0}
                }
                
                cmdb_doc = self.cmdb_updater.transform_oracle_data(data, system_data, "REMOTE_VBOX")
                
                # Force preserve the original inventory name (NEXI-ORACLE-RAC1/2)
                original_name = identity.get('db_unique_name')
                if original_name:
                    cmdb_doc['identity']['db_unique_name'] = original_name

                # Preserve original connection info as transform might overwrite identity
                if 'connection' not in cmdb_doc:
                    cmdb_doc['connection'] = conn
                
                # Ensure status is UP
                if 'state' not in cmdb_doc: cmdb_doc['state'] = {}
                cmdb_doc['state']['status'] = 'UP'
                
                self.cmdb_updater.upsert_database(cmdb_doc)
                print(f"   ✅ Deep Oracle Data updated for {identity.get('db_unique_name')}")
                return True
            else:
                print(f"   ⚠️ No data collected from {host}")
                return False
                
        except Exception as e:
            print(f"   ❌ Remote Collection Error: {e}")
            return False

    def run_once(self):
        print("📊 Collector: Starting metrics gathering cycle...")
        inventory = self.mongo.get_inventory()
        if not inventory:
            print("   Inventory empty. Skipping.")
            return

        count = 0
        for db in inventory:
            identity = db.get('identity', {})
            name = identity.get('db_unique_name')
            engine = identity.get('engine', 'UNKNOWN')
            is_remote = db.get('connection', {}).get('type') == 'REMOTE' or 'vbox' in name.lower()
            
            try:
                # 1. Handle Remote Oracle
                if engine == 'ORACLE' and is_remote:
                    if self.collect_remote_oracle(db):
                        count += 1
                    continue

                # 2. Handle Docker Containers
                # FIX: Use connection.container as primary source of truth (handles hyphens vs underscores)
                container_name = db.get('connection', {}).get('container')
                
                # Fallback to identity.db_name
                if not container_name:
                    container_name = identity.get('db_name')
                
                # Final fallback
                if not container_name:
                    container_name = name.lower() if name else None
                
                if container_name:
                    # FIX: Strict check for running state (Windows Docker output fix)
                    if self.is_container_running(container_name):
                        # Always mark UP if running, even if metrics fail
                        self.mongo.update_status(name, "UP")
                        
                        metrics = self.collect_docker_metrics(container_name)
                        if metrics:
                            print(f"   📈 Metrics for {name}: CPU={metrics['cpu_usage']}, RAM={metrics['ram_usage']}")
                            self.mongo.update_metrics(name, metrics)
                            count += 1
                        else:
                             print(f"   ⚠️ Metrics collection failed for {name} (Running but no stats?)")
                    else:
                        if not is_remote:
                            print(f"   🛑 Container {container_name} is stopped. Marking DOWN.")
                            self.mongo.update_status(name, "DOWN")

            except Exception as e:
                print(f"   ❌ Error processing {name}: {e}")
                continue
        
        print(f"✅ Metric Sync Complete. Updated {count} assets.")

    def run_continuous(self, interval=30):
        print(f"🔄 Collector Agent running continuously (Interval: {interval}s)...")
        while True:
            self.run_once()
            time.sleep(interval)

if __name__ == "__main__":
    agent = CollectorAgent()
    # Check if run once
    if "--once" in sys.argv:
        agent.run_once()
    else:
        agent.run_continuous()
