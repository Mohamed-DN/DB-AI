
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Orchestrator'))
from src.mongo_proxy import MongoProxy

def fix_container_names():
    mongo = MongoProxy()
    
    updates = [
        ("M-DN-PG-MILANO-DEV", "m-dn-pg-milano-dev"),
        ("M-DN-PG-BRATISLAVA-DEV", "m-dn-pg-bratislava-dev"),
        # Also check STG if it exists
        ("M-DN-PG-MILANO-STG", "m-dn-pg-milano-stg")
    ]
    
    print("Fixing missing db_name (container name)...")
    
    for db_unique_name, container_name in updates:
        print(f"Updating {db_unique_name} -> {container_name}")
        # Only update if it exists
        mongo.execute_eval(f"""
        db.inventory_databases.updateOne(
            {{ "identity.db_unique_name": "{db_unique_name}" }},
            {{ $set: {{ "identity.db_name": "{container_name}" }} }}
        )
        """)
    
    print("Fix Complete.")

if __name__ == "__main__":
    fix_container_names()
