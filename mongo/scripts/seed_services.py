import sys
import os
import json
sys.path.append(os.getcwd())
from Orchestrator.src.mongo_proxy import MongoProxy

try:
    m = MongoProxy()
    
    # 1. Get all DBs to map
    dbs = m.execute_eval("db.inventory_databases.find().toArray()")
    db_names = [d.get('identity', {}).get('db_unique_name') for d in dbs if d.get('identity', {}).get('db_unique_name')]
    
    print(f"Found DBs to map: {db_names}")
    
    # 2. Create Default Service
    # Only if empty
    existing = m.execute_eval("db.business_services.countDocuments({})")
    if existing == 0:
        service_doc = {
            "name": "General IT Infrastructure",
            "description": "Core database infrastructure",
            "contacts": {
                "bao": {"name": "Admin", "email": "admin@m-dn.it", "phone": "+390234567890", "department": "IT Ops"},
                "dl_team": "db-admins@m-dn.it"
            },
            "snow_group": "DBA_L2_SUPPORT",
            "reperibility_number": "+39000111222",
            "technical_mapping": {
                # Map all found DBs to this service
                "db_unique_name": "ALL" # Logic in CriticalAlert might need specific names, let's look at code.
                # Code uses: findOne({'technical_mapping.db_unique_name': db_name})
                # So we need one doc PER db, or one doc with ARRAY?
                # Code uses: findOne ... so it expects direct match.
            }
        }
        
        # Create one service doc per DB for now to be safe, or one doc with multiple entries?
        # The query is `technical_mapping.db_unique_name': 'NAME'`.
        # If I want one service to cover multiple, I should look at CriticalAlert logic again.
        # It's findOne. If db_unique_name is inside an array? MongoDB handles unnesting?
        # Yes, if `technical_mapping.db_unique_name` is an array: ["DB1", "DB2"], query matches.
        
        service_doc["technical_mapping"]["db_unique_name"] = db_names
        
        m.execute_eval(f"db.business_services.insertOne({json.dumps(service_doc)})")
        print("✅ Created Default Business Service mapping for ALL databases.")
        
    else:
        print("Business Services start exist. Updating mapping and schema...")
        # Update existing to include all current DBs AND upgrade schema with new fields
        # Using $set for fields and $addToSet for mappings
        update_doc = {
            "snow_group": "DBA_L2_SUPPORT",
            "reperibility_number": "+39000111222",
            "contacts.bao.phone": "+390234567890", 
            "contacts.bao.department": "IT Ops"
        }
        
        m.execute_eval(f"db.business_services.updateMany({{}}, {{ $addToSet: {{ 'technical_mapping.db_unique_name': {{ $each: {json.dumps(db_names)} }} }}, $set: {json.dumps(update_doc)} }})")
        print("✅ Updated mappings and upgraded schema.")

except Exception as e:
    import json # fallback import
    print(f"Error: {e}")
