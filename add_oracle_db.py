"""
Add Remote Oracle Database to Inventory
Usage: python add_oracle_db.py
"""
import sys
import os
import getpass

# Link to Shared Modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Orchestrator/src')))
# We might need to adjust path depending on where we run this.
# Assuming running from root (c:\AI-Nexi\Nexi_DB_AI)

try:
    from Orchestrator.src.mongo_proxy import MongoProxy
except ImportError:
    sys.path.append(os.path.abspath('Orchestrator/src'))
    from mongo_proxy import MongoProxy

def add_db():
    print("=== Add Remote Oracle Database (VirtualBox) ===")
    
    while True:
        print("\n--- Enter Database Details (Ctrl+C to exit) ---")
        host = input("Host IP [192.168.56.101]: ").strip()
        if not host: host = "192.168.56.101"
        
        port_str = input("Port [1521]: ").strip()
        port = int(port_str) if port_str else 1521
        
        service = input("Service Name / SID [orcl]: ").strip()
        if not service: service = "orcl"
        
        user = input("Username [oracle]: ").strip()
        if not user: user = "oracle"
        
        # Simple hiding of password input
        password = getpass.getpass("Password: ")
        
        name = input(f"Unique Name [ORACLE-{host}]: ").strip().upper()
        if not name: name = f"ORACLE-{host}-{service}".upper()
        
        # Create Doc
        doc = {
            "identity": {
                "db_unique_name": name,
                "db_name": service,
                "engine": "ORACLE",
                "environment": "DEV", 
                "topology": "SINGLE"
            },
            "connection": {
                "type": "REMOTE",
                "host": host,
                "port": port,
                "service_name": service,
                "user": user,
                "password": password
            },
            "state": {
                "status": "UNKNOWN",
                "metrics": {}
            }
        }
        
        print(f"\nAdding {name} ({host}:{port}/{service})...")
        
        mongo = MongoProxy()
        # Check if exists
        exists = mongo.execute_eval(f"db.inventory_databases.findOne({{'identity.db_unique_name': '{name}'}})")
        if exists:
            print(f"❌ Database {name} already exists! Updating...")
            
        # Insert/Update
        import json
        doc_json = json.dumps(doc)
        mongo.execute_eval(f"db.inventory_databases.updateOne({{'identity.db_unique_name': '{name}'}}, {{$set: {doc_json}}}, {{upsert: true}})")
        
        print("✅ Database Added!")
        
        cont = input("\nAdd another? (y/n) [y]: ").lower()
        if cont == 'n': break

if __name__ == "__main__":
    add_db()
