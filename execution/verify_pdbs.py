import sys
import os
import json

# Add path to Orchestrator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Orchestrator/src')))
# Also add root for relative imports inside MongoProxy if needed
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from mongo_proxy import MongoProxy
    mongo = MongoProxy()
    
    print("--- Querying via MongoProxy ---")
    
    # Dump all hosts
    print("\n--- HOSTS & METRICS ---")
    all_dbs = mongo.execute_eval("db.inventory_databases.find().toArray()")
    if all_dbs:
        for db in all_dbs:
            name = db.get("identity", {}).get("db_unique_name")
            host = db.get("state", {}).get("metrics", {}).get("hostname", "N/A")
            print(f"DB: {name} | Host: {host} | Metrics: {bool(db.get('state', {}).get('metrics'))}")
            
            # If RAC, print config keys
            if "RAC" in name:
                print(f"   Config Keys: {db.get('configuration', {}).keys()}")
                print(f"   Oracle Specific: {db.get('configuration', {}).get('oracle_specific', {})}")

except Exception as e:
    print(f"Error: {e}")
