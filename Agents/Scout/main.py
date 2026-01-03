"""
Scout Agent - Discovers active databases in Docker and updates Inventory
"""
import sys
import os
import json
import subprocess
import datetime
import time

# Add path for shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from Orchestrator.src.mongo_proxy import MongoProxy

class ScoutAgent:
    def __init__(self):
        self.mongo = MongoProxy()
        
    def scan_docker(self):
        """Scan Docker for database containers"""
        print("🛰️ Scout scanning Docker environment...")
        try:
            # List all containers with formatting to get names and ports
            cmd = ["docker", "ps", "--format", "{{.Names}}|{{.Ports}}|{{.Image}}"]
            output = subprocess.check_output(cmd).decode('utf-8').strip()
            
            found_dbs = []
            
            for line in output.split('\n'):
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
                    # Extract external port
                    port = 5432 # Default
                    if "->" in ports_str:
                        try:
                            parts = ports_str.split('->')[0]
                            port = int(parts.split(':')[-1])
                        except:
                            pass
                    
                    db_info = {
                        "identity": {
                            "db_unique_name": name.upper(),
                            "db_name": name,
                            "engine": engine,
                            "environment": "DEV" if "dev" in name.lower() else "PROD",
                            "host": "127.0.0.1"
                        },
                        "configuration": {
                            "port": port,
                            "version": "Unknown"
                        },
                        "last_scanned": "NOW"
                    }
                    found_dbs.append(db_info)
                    
            return found_dbs
            
        except Exception as e:
            print(f"❌ Scout Error: {e}")
            return []

    def update_inventory(self, dbs):
        """Update MongoDB Inventory"""
        print(f"💾 Updating Inventory with {len(dbs)} databases...")
        
        # Get existing DBs
        existing_docs = self.mongo.execute_eval("db.inventory_databases.find({}, {'identity.db_unique_name': 1}).toArray()")
        existing_names = set()
        if existing_docs:
            for doc in existing_docs:
                if 'identity' in doc and 'db_unique_name' in doc['identity']:
                    existing_names.add(doc['identity']['db_unique_name'])
        
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

            # Upsert (Always update status to UP)
            db_json = json.dumps(db)
            db_json = db_json.replace('"NOW"', 'new Date()')
            
            js_cmd = f"""
            db.inventory_databases.updateOne(
                {{ "identity.db_unique_name": "{name}" }},
                {{ $set: {db_json}, $set: {{"state.status": "UP", "state.last_seen": new Date()}} }},
                {{ upsert: true }}
            )
            """
            self.mongo.execute_eval(js_cmd)
        
        # Check MISSING
        missing_names = existing_names - found_names
        for missing in missing_names:
            print(f"⚠️ DETECTED MISSING ASSET: {missing}")
            js_cmd = f"""
            db.inventory_databases.updateOne(
                {{ "identity.db_unique_name": "{missing}" }},
                {{ $set: {{"state.status": "MISSING", "state.last_seen": new Date()}} }}
            )
            """
            self.mongo.execute_eval(js_cmd)
            
            # Create Alert
            alert = {
                "severity": "CRITICAL",
                "state": "CRITICAL",
                "type": "ASSET_MISSING",
                "host_name": "Docker",
                "service": f"DB-{missing}",
                "message": f"Database {missing} was not found in Docker scan.",
                "output": "Container Missing",
                "timestamp": "NOW",
                "processed": False
            }
            self.mongo.insert_alert(alert)
        
        print(f"✅ Inventory Sync Complete. Found: {len(found_names)}, Missing: {len(missing_names)}")

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

    def run_continuous(self):
        """Run loop"""
        print("🛰️ Scout Agent starting continuous monitoring...")
        while True:
            try:
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
