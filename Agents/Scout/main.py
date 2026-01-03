"""
Scout Agent - Discovers active databases in Docker and updates Inventory
"""
import sys
import os
import json
import subprocess
import datetime

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
                    # Skip mongo itself usually, but let's list it for fun, 
                    # though CriticalAlert might not know how to check it yet.
                    pass 
                
                if engine and "gateway" not in name:
                    # Extract external port
                    # Format: 0.0.0.0:5433->5432/tcp
                    port = 5432 # Default
                    if "->" in ports_str:
                        try:
                            # Parse '0.0.0.0:5433->5432/tcp' or '5433->5432/tcp'
                            parts = ports_str.split('->')[0]
                            port = int(parts.split(':')[-1])
                        except:
                            pass
                    
                    db_info = {
                        "identity": {
                            "db_unique_name": name.upper(),
                            "db_name": name, # Simplification
                            "engine": engine,
                            "environment": "DEV" if "dev" in name.lower() else "PROD",
                            "host": "127.0.0.1" # Localhost since we run agents locally against docker mapped ports
                        },
                        "configuration": {
                            "port": port,
                            "version": "Unknown"
                        },
                        "last_scanned": "NOW" # Placeholder for Date
                    }
                    found_dbs.append(db_info)
                    
            return found_dbs
            
        except Exception as e:
            print(f"❌ Scout Error: {e}")
            return []

    def update_inventory(self, dbs):
        """Update MongoDB Inventory"""
        print(f"💾 Updating Inventory with {len(dbs)} databases...")
        new_count = 0
        
        # Get existing to check for new ones
        existing_docs = self.mongo.execute_eval("db.inventory_databases.find({}, {'identity.db_unique_name': 1}).toArray()")
        existing_names = set()
        if existing_docs:
            for doc in existing_docs:
                if 'identity' in doc and 'db_unique_name' in doc['identity']:
                    existing_names.add(doc['identity']['db_unique_name'])

        for db in dbs:
            # Check if new
            name = db['identity']['db_unique_name']
            if name not in existing_names:
                print(f"✨ NEW DATABASE FOUND: {name}")
                new_count += 1
                
                # Create alert for new DB
                alert = {
                    "severity": "WARNING",
                    "state": "WARNING",
                    "type": "NEW_DB_DISCOVERED",
                    "host_name": db['identity']['host'],
                    "service": f"{db['identity']['engine']}-{name}",
                    "message": f"Scout discovered new {db['identity']['engine']} database: {name} on port {db['configuration']['port']}",
                    "output": f"New Asset: {name}",
                    "timestamp": "NOW",
                    "processed": False
                }
                self.mongo.insert_alert(alert)

            # Upsert into Inventory
            # JS command to update
            # We construct a JS object string carefully
            db_json = json.dumps(db)
            # Replace "NOW" with new Date()
            db_json = db_json.replace('"NOW"', 'new Date()')
            
            js_cmd = f"""
            db.inventory_databases.updateOne(
                {{ "identity.db_unique_name": "{name}" }},
                {{ $set: {db_json} }},
                {{ upsert: true }}
            )
            """
            self.mongo.execute_eval(js_cmd)
            
        print(f"✅ Inventory Updated. {new_count} new assets.")

    def run(self):
        dbs = self.scan_docker()
        if dbs:
            self.update_inventory(dbs)
        else:
            print("No databases found.")

if __name__ == "__main__":
    agent = ScoutAgent()
    agent.run()
