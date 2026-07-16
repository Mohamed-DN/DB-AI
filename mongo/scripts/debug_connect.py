
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Orchestrator'))
from src.mongo_proxy import MongoProxy

def check_db():
    mongo = MongoProxy()
    
    # Check Milano DEV
    name = "M-DN-PG-MILANO-DEV"
    print(f"Checking {name}...")
    doc = mongo.execute_eval(f"db.inventory_databases.findOne({{ 'identity.db_unique_name': '{name}' }})")
    
    if doc:
        print("Found Document.")
        ident = doc.get('identity', {})
        print(f"Identity: {ident}")
        container = ident.get('db_name')
        print(f"Target Container: {container}")
        
        if not container:
            print("❌ ERROR: identity.db_name (Container Name) is MISSING!")
    else:
        print("❌ ERROR: Document not found!")

    # Check Bratislava DEV
    name = "M-DN-PG-BRATISLAVA-DEV"
    print(f"\nChecking {name}...")
    doc = mongo.execute_eval(f"db.inventory_databases.findOne({{ 'identity.db_unique_name': '{name}' }})")
    if doc:
        ident = doc.get('identity', {})
        container = ident.get('db_name')
        print(f"Target Container: {container}")
    else:
        print("❌ ERROR: Document not found!")

if __name__ == "__main__":
    check_db()
