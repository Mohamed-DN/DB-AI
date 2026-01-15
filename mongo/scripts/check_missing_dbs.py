
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Orchestrator'))
from src.mongo_proxy import MongoProxy

def check_missing():
    mongo = MongoProxy()
    print("Checking ALL databases...")
    dbs = mongo.execute_eval("db.inventory_databases.find().toArray()")
    print(f"Found {len(dbs)} databases:")
    for db in dbs:
        name = db.get('identity', {}).get('db_unique_name')
        status = db.get('state', {}).get('status')
        print(f" - {name}: {status}")

if __name__ == "__main__":
    check_missing()
