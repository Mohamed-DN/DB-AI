
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Orchestrator'))
from src.mongo_proxy import MongoProxy

def check_service_mapping():
    mongo = MongoProxy()
    name = "M-DN-PG-MILANO-STG"
    print(f"Checking Business Service mapping for {name}...")
    
    service = mongo.execute_eval(f"db.business_services.findOne({{ 'technical_mapping.db_unique_name': '{name}' }})")
    
    if service:
        print(f"✅ Found Service: {service.get('name')}")
        contacts = service.get('contacts', {})
        print(f"   Contacts: {contacts}")
        
    else:
        print("❌ No Business Service found for this database!")
        print("   CriticalAlert will NOT send emails because it doesn't know who to contact.")

    # List all services to see what we have
    print("\n--- All Services ---")
    all_services = mongo.execute_eval("db.business_services.find().toArray()")
    for s in all_services:
        dbs = s.get('technical_mapping', {}).get('db_unique_name', [])
        print(f"Service: {s.get('name')} -> DBs: {dbs}")

if __name__ == "__main__":
    check_service_mapping()
