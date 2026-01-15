import sys
import os
sys.path.append(os.getcwd())
from Orchestrator.src.mongo_proxy import MongoProxy

try:
    m = MongoProxy()
    
    # Debug counts
    print("--- COUNTS ---")
    total = m.execute_eval("db.inventory_databases.countDocuments({})")
    print(f"Total Docs: {total}")
    
    mongos = m.execute_eval("db.inventory_databases.countDocuments({'identity.db_unique_name': {$regex: 'mongo', $options: 'i'}})")
    print(f"Mongo Docs by Name: {mongos}")
    
    # Delete specific redundant ones as requested
    targets = ['mongodb', 'nexi-mongodb', 'nexi-mongo-express']
    
    for t in targets:
        # Check if exists
        exists = m.execute_eval(f"db.inventory_databases.findOne({{'identity.db_unique_name': '{t}'}})")
        if exists:
            print(f"Found {t}. Deleting...")
            m.execute_eval(f"db.inventory_databases.deleteOne({{'identity.db_unique_name': '{t}'}})")
            print(f"Deleted {t}.")
        else:
            print(f"{t} not found by exact name.")
            
        # Also check by container name
        exists_cont = m.execute_eval(f"db.inventory_databases.findOne({{'connection.container': '{t}'}})")
        if exists_cont:
            print(f"Found container {t}. Deleting...")
            m.execute_eval(f"db.inventory_databases.deleteOne({{'connection.container': '{t}'}})")
            print(f"Deleted container {t}.")

except Exception as e:
    print(f"Error: {e}")
