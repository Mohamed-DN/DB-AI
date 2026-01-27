"""
Scout Agent - Discovers active databases in Docker and updates Inventory
"""
import sys
import os
import json
import subprocess
import datetime
import time

# Force UTF-8 for Windows Console
sys.stdout.reconfigure(encoding='utf-8')

# Add path for shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from api_agents.shared.sync_mongo_service import SyncMongoService
from api_agents.shared.redis_client import RedisClient
from api_agents.workers.scout.template_loader import build_document

class ScoutAgent:
    def __init__(self):
        self.mongo = SyncMongoService.get_instance()
        self.redis = RedisClient.get_instance()
        
    def scan_docker(self):
        """Scan Docker for database containers"""
        print("🛰️ Scout scanning Docker environment...")
        try:
            # List all containers with formatting to get names and ports
            cmd = ["docker", "ps", "--format", "{{.Names}}|{{.Ports}}|{{.Image}}"]
            output = subprocess.check_output(cmd).decode('utf-8').strip()
            
            # Pass 1: Identify Active Gateways
            active_gateways = set()
            lines = output.split('\n')
            for line in lines:
                if not line: continue
                name, _, _ = line.split('|')
                if "gw" in name or "gateway" in name:
                    active_gateways.add(name)
            
            print(f"🌉 Active Gateways: {active_gateways}")

            found_dbs = []
            
            # Pass 2: Identify Databases and check Gateway dependency
            # V2 Support: Use GATEWAY_SUFFIX env var (default "" for V1, "2" for V2)
            gw_suffix = os.environ.get("GATEWAY_SUFFIX", "")
            gateway_map = {
                "MILANO": f"nexi-gw-milano{gw_suffix}",
                "BRATISLAVA": f"nexi-gw-bratislava{gw_suffix}",
                "CAIRO": f"nexi-gw-cairo{gw_suffix}"
            }

            for line in lines:
                if not line: continue
                name, ports_str, image = line.split('|')
                
                # Simple logic to identify DBs
                engine = None
                if "postgres" in image or "postgres" in name:
                    engine = "POSTGRES"
                elif "oracle" in image or "oracle" in name:
                    engine = "ORACLE"
                elif "mongo" in image and "express" not in image: 
                    pass 
                
                if engine and "gateway" not in name:
                    # CHECK GATEWAY DEPENDENCY (mandatory)
                    region_found = False
                    gateway_ref = None
                    is_reachable = True
                    for region, gw_name in gateway_map.items():
                        if region in name.upper():
                            region_found = True
                            gateway_ref = gw_name
                            if gw_name not in active_gateways:
                                is_reachable = False
                                print(f"BLOCKED: {name} (Gateway {gw_name} is MISSING from {active_gateways})")
                                break
                            else:
                                print(f"ALLOWED: {name} (Gateway {gw_name} is UP)")

                    if not region_found:
                        print(f"BLOCKED: {name} missing gateway mapping (mandatory)")
                        continue

                    if not is_reachable:
                        print(f"SKIPPING: {name} due to Gateway Failure")
                        continue
                    # Extract external port
                    port = 5432 # Default
                    if "->" in ports_str:
                        try:
                            parts = ports_str.split('->')[0]
                            port = int(parts.split(':')[-1])
                        except:
                            pass
                    
                    # Determine environment
                    if "dev" in name.lower():
                        environment = "DEVELOPMENT"
                    elif "stg" in name.lower():
                        environment = "STAGING"
                    else:
                        environment = "PRODUCTION"
                    
                    # Build hierarchical document using template
                    db_info = build_document(
                        engine=engine,
                        container_name=name,
                        port=port,
                        environment=environment,
                        gateway_ref=gateway_ref
                    )
                    found_dbs.append(db_info)
                    
            return found_dbs
            
        except Exception as e:
            print(f"❌ Scout Error: {e}")
            return []

    def run(self):
        dbs = self.scan_docker()
        if dbs:
            print(f"📡 Found {len(dbs)} databases. Pushing to Discovery Queue...")
            self.redis.push_to_queue("DISCOVERY_UPDATES", {"dbs": dbs})
            print("✅ Discovery payload pushed to Redis.")
        else:
            print("No databases found.")

    def get_interval(self):
        """Get scan interval from MongoDB Config"""
        try:
            interval = self.mongo.get_config('scout_interval')
            if interval:
                return int(interval)
        except:
            pass
        return 60 # Default 60s

    def check_pause(self):
        """Check if system is globally paused"""
        try:
            doc = self.mongo.execute_eval("db.system_config.findOne({key: 'global_status'})")
            if doc and doc.get('value') == 'PAUSED':
                return True
        except:
            pass
        return False

    def run_continuous(self):
        """Run loop"""
        print("🛰️ Scout Agent starting continuous monitoring...")
        while True:
            try:
                if self.check_pause():
                    print("⏸️ System Global Pause Active. Scout sleeping...")
                    time.sleep(10)
                    continue

                interval = self.get_interval()
                self.run()
                print(f"💤 Sleeping for {interval}s...")
                time.sleep(interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    agent = ScoutAgent()
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    
    if args.once:
        agent.run()
    else:
        agent.run_continuous()
