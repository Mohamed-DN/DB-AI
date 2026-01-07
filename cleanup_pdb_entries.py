import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Orchestrator/src')))

from mongo_proxy import MongoProxy

mongo = MongoProxy()

print("Deleting duplicate PDB inventory entries...")
result = mongo.execute_eval("db.inventory_databases.deleteMany({'identity.topology': 'PDB'})")
print(f"Result: {result}")

print("\nRemaining databases:")
dbs = mongo.execute_eval("db.inventory_databases.find({}, {'identity.db_unique_name': 1}).toArray()")
for db in dbs:
    print(f"  - {db.get('identity', {}).get('db_unique_name')}")
