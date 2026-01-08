import sys
import os
import json
sys.path.append(os.getcwd())
try:
    from Orchestrator.src.mongo_proxy import MongoProxy
    m = MongoProxy()
    
    print("--- INVENTORY ---")
    inv = m.execute_eval("db.inventory_databases.find({$or: [{'identity.db_unique_name': /mongo/i}, {'connection.container': /mongo/i}]}).toArray()")
    print(json.dumps(inv, indent=2, default=str))
    
    print("--- DISCOVERY ---")
    disc = m.execute_eval("db.discovery_queue.find({$or: [{'service': /mongo/i}, {'container_name': /mongo/i}]}).toArray()")
    print(json.dumps(disc, indent=2, default=str))

except Exception as e:
    print(f"Error: {e}")
