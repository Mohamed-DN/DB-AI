
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Orchestrator'))
from src.mongo_proxy import MongoProxy

def set_global_bao():
    mongo = MongoProxy()
    print("Configuring Global BAO (You) for ALL Databases...")

    # 1. Get ALL DB Unique Names
    dbs = mongo.execute_eval("db.inventory_databases.find({}, {'identity.db_unique_name': 1}).toArray()")
    all_db_names = [d.get('identity', {}).get('db_unique_name') for d in dbs if d.get('identity', {}).get('db_unique_name')]
    
    if not all_db_names:
        print("Error: No databases found in inventory! Run Scout first.")
        return

    print(f"Found {len(all_db_names)} Databases: {all_db_names}")

    # 2. Create/Overlap a "Master Service" that covers everything
    # We use $addToSet to merge, ensuring we don't lose coverage if we run this multiple times
    
    master_service = {
        "name": "Global Operations (Master)",
        "description": "Catch-all service for User Administration",
        "contacts": {
            "bao": {
                "name": "Admin User",
                "email": "bao@m-dn.lab"
            },
            "dl_team": "alerts@m-dn.lab"
        },
        "technical_mapping": {
            "db_unique_name": all_db_names # Overwrite list to ensure full coverage
        }
    }

    # Upsert based on name
    mongo.execute_eval(f"""
    db.business_services.updateOne(
        {{ name: 'Global Operations (Master)' }},
        {{ $set: {master_service} }},
        {{ upsert: true }}
    )
    """)
    
    print("GLOBAL BAO SET PERMANENTLY.")
    print("   Any database alert will now route to 'bao@m-dn.lab'.")
    print("   Check the 'emails' folder for generated alerts.")

if __name__ == "__main__":
    set_global_bao()
