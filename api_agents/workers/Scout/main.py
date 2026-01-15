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
from orchestrator.core.mongo_proxy import MongoProxy
from api_agents.workers.Scout.user_provisioner import UserProvisioner
from api_agents.workers.Scout.template_loader import build_document

class ScoutAgent:
    def __init__(self):
        self.mongo = MongoProxy()
        self.provisioner = UserProvisioner(self.mongo)
        
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

    def update_inventory(self, dbs):
        """Update MongoDB Inventory"""
        print(f"💾 Updating Inventory with {len(dbs)} databases...")
        
        # Get existing DBs with status
        existing_docs = self.mongo.execute_eval("db.inventory_databases.find({}, {'identity.db_unique_name': 1, 'state.status': 1}).toArray()")
        existing_names = set()
        existing_status = {}
        if existing_docs:
            for doc in existing_docs:
                if 'identity' in doc and 'db_unique_name' in doc['identity']:
                    name = doc['identity']['db_unique_name']
                    existing_names.add(name)
                    # Safe get status
                    try:
                        status = doc.get('state', {}).get('status', 'UNKNOWN')
                        existing_status[name] = status
                    except:
                        existing_status[name] = 'UNKNOWN'
        
        found_names = set()
        for db in dbs:
            name = db['identity']['db_unique_name']
            found_names.add(name)
            
            # Check if NEW
            if name not in existing_names:
                print(f"✨ NEW DATABASE FOUND: {name}")
                alert = {
                    "severity": "WARNING",
                    "state": "WARNING",
                    "type": "NEW_DB_DISCOVERED",
                    "host_name": db['identity']['host'],
                    "service": f"{db['identity']['engine']}-{name}",
                    "message": f"Scout discovered new {db['identity']['engine']} database: {name}",
                    "output": "New Asset",
                    "timestamp": "NOW",
                    "processed": False
                }
                self.mongo.insert_alert(alert)
                
                # 🔑 AUTO-PROVISION AIAUTO USER
                try:
                    prov_result = self.provisioner.provision_database(db)
                    if prov_result.get('provisioned'):
                        print(f"✅ AIAUTO user provisioned on {name}")
                    elif prov_result.get('skipped'):
                        print(f"⏭️ Skipped provisioning for {name}: {prov_result.get('reason')}")
                    else:
                        print(f"⚠️ Provisioning failed for {name}: {prov_result.get('message', prov_result.get('error'))}")
                except Exception as prov_err:
                    print(f"❌ Provisioning error for {name}: {prov_err}")

            # Check if NEW or EXISTING for Update Logic
            if name in existing_names:
                # EXISTING: Check for RECOVERY
                prev_status = existing_status.get(name, 'UNKNOWN')
                if prev_status in ['MISSING', 'DOWN']:
                    print(f"🎉 RECOVERY DETECTED: {name} is back UP (was {prev_status})")
                    alert = {
                        "severity": "RESOLVED",
                        "state": "RESOLVED", 
                        "type": "DB_RECOVERY",
                        "db_unique_name": name,
                        "host_name": db['identity']['host'],
                        "service": f"{db['identity']['engine']}-{name}",
                        "message": f"Database {name} has recovered and is back ONLINE.",
                        "output": "Service Restored",
                        "timestamp": "NOW",
                        "processed": False
                    }
                    self.mongo.insert_alert(alert)

                # Only update state/status, preserve manual metadata
                js_cmd = f"""
                db.inventory_databases.updateOne(
                    {{ "identity.db_unique_name": "{name}" }},
                    {{ $set: {{ "state.status": "UP", "state.last_seen": new Date() }} }}
                )
                """
            else:
                # NEW: Full Upsert
                db_json = json.dumps(db)
                db_json = db_json.replace('"NOW"', 'new Date()')
                
                js_cmd = f"""
                db.inventory_databases.updateOne(
                    {{ "identity.db_unique_name": "{name}" }},
                    {{ $set: {db_json}, $set: {{ "state.status": "UP", "state.last_seen": new Date() }} }},
                    {{ upsert: true }}
                )
                """
            self.mongo.execute_eval(js_cmd)
        
        # Check MISSING - but exclude REMOTE databases (e.g. VirtualBox Oracle RAC)
        # Get remote DBs to exclude
        remote_dbs_result = self.mongo.execute_eval("db.inventory_databases.find({'connection.type': 'REMOTE'}, {'identity.db_unique_name': 1}).toArray()")
        remote_names = set()
        if remote_dbs_result:
            for doc in remote_dbs_result:
                name = doc.get('identity', {}).get('db_unique_name')
                if name:
                    remote_names.add(name)
        
        missing_names = existing_names - found_names - remote_names
        # print(f"📉 Missing Candidates: {missing_names}") # verbose
        for missing in missing_names:
            prev_status = existing_status.get(missing, 'UNKNOWN')
            
            # Update status to MISSING
            js_cmd = f"db.inventory_databases.updateOne({{ 'identity.db_unique_name': '{missing}' }}, {{ $set: {{ 'state.status': 'MISSING', 'state.last_seen': new Date() }} }})"
            self.mongo.execute_eval(js_cmd)
            
            # Anti-Spam: Only alert if it's a NEW incident
            if prev_status != 'MISSING':
                print(f"⚠️ DETECTED MISSING ASSET: {missing} (Prev: {prev_status})")
                
                # Create Alert
                alert = {
                    "severity": "CRITICAL",
                    "state": "CRITICAL",
                    "type": "ASSET_MISSING",
                    "db_unique_name": missing,
                    "host_name": "Docker",
                    "service": f"DB-{missing}",
                    "message": f"Database {missing} was not found in Docker scan.",
                    "output": "Container Missing",
                    "timestamp": "NOW",
                    "processed": False
                }
                self.mongo.insert_alert(alert)
            else:
                pass # Already known missing, silent update
        
        print(f"✅ Inventory Sync Complete. Found: {len(found_names)}, Missing: {len(missing_names)}, Remote (Excluded): {len(remote_names)}")

    def run(self):
        dbs = self.scan_docker()
        if dbs:
            self.update_inventory(dbs)
        else:
            print("No databases found.")

    def get_interval(self):
        """Get scan interval from MongoDB Config"""
        try:
            cmd = "db.system_config.findOne({key: 'scout_interval'})"
            doc = self.mongo.execute_eval(cmd)
            if doc and 'value' in doc:
                return int(doc['value'])
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
