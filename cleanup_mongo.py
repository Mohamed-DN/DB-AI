import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Orchestrator/src')))

try:
    from mongo_proxy import MongoProxy
    mongo = MongoProxy()
    print("Deleting duplicate 'cdbrac' entry...")
    res = mongo.execute_eval("db.inventory_databases.deleteOne({'identity.db_unique_name': 'cdbrac'})")
    print(res)
    
except Exception as e:
    print(f"Error: {e}")
