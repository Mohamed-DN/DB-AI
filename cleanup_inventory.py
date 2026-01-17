import asyncio
import os
import sys

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '')))

from api_agents.api_gateway.services.mongo_service import get_mongo_service

async def cleanup():
    mongo = get_mongo_service()
    print("🧹 Cleaning Inventory...")
    
    # 1. Delete all entries that don't look like our real containers
    # Real ones start with 'nexi-' and have specific types
    result = await mongo.db.inventory_databases.delete_many({
        "$or": [
            {"identity.db_unique_name": None},
            {"identity.db_unique_name": "UNKNOWN"},
            {"identity.db_unique_name": {"$not": {"$regex": "^(nexi-pg|nexi-oracle|nexi-redis|nexi-qdrant|nexi-mongo|NEXI-PG|NEXI-ORACLE|NEXI-REDIS|NEXI-QDRANT|NEXI-MONGO)"}}}
        ]
    })
    print(f"🗑️ Deleted {result.deleted_count} invalid/mock entries.")

    # 2. De-duplicate remaining real entries
    # Use direct access to get _id
    cursor = mongo.db.inventory_databases.find({})
    dbs = await cursor.to_list(length=None)
    
    seen = {}
    duplicates = []
    
    for db in dbs:
        name = db.get('identity', {}).get('db_unique_name')
        if not name: continue
        
        if '_id' not in db:
            print(f"⚠️ Warning: Document missing _id: {db.keys()}")
            continue

        if name in seen:
            duplicates.append(db['_id'])
        else:
            seen[name] = True
            
    if duplicates:
        print(f"found {len(duplicates)} duplicates for valid names. Removing...")
        await mongo.db.inventory_databases.delete_many({"_id": {"$in": duplicates}})
        print("✅ Duplicates removed.")
    else:
        print("✅ No duplicates found.")

    print("Populating initial real inventory if empty...")
    if len(seen) == 0:
        # Seed basic if totally empty (fallback)
        pass 
        
if __name__ == "__main__":
    asyncio.run(cleanup())
