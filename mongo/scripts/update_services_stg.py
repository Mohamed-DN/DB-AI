
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Orchestrator'))
from src.mongo_proxy import MongoProxy

def update_services():
    mongo = MongoProxy()
    
    # Target: Payments Core (Milano)
    # Add M-DN-PG-MILANO-STG to its database list
    
    print("Updates Payments Core service...")
    
    # 1. Find the service
    service = mongo.execute_eval("db.business_services.findOne({name: 'Payments Core'})")
    if not service:
        print("Service 'Payments Core' not found. Creating generic one...")
        # Fallback if needed, but it should exist
        return

    # 2. Update
    mongo.execute_eval("""
    db.business_services.updateOne(
        { name: 'Payments Core' },
        { $addToSet: { "technical_mapping.db_unique_name": "M-DN-PG-MILANO-STG" } }
    )
    """)
    
    print("Added M-DN-PG-MILANO-STG to Payments Core.")
    
    # Verify
    s = mongo.execute_eval("db.business_services.findOne({name: 'Payments Core'})")
    print("Current DBs:", s.get('technical_mapping', {}).get('db_unique_name'))

if __name__ == "__main__":
    update_services()
