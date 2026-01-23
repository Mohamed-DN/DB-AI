import asyncio
import os
import sys

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '')))

from api_agents.api_gateway.services.mongo_service import get_mongo_service

async def main():
    mongo = get_mongo_service()
    dbs = await mongo.get_inventory()
    print(f"Total DBs: {len(dbs)}")
    
    names = {}
    for db in dbs:
        name = db.get('identity', {}).get('db_unique_name', 'UNKNOWN')
        _id = str(db.get('_id'))
        if name not in names:
            names[name] = []
        names[name].append(_id)
        
    print("\n--- Duplicates ---")
    for name, ids in names.items():
        if len(ids) > 1:
            print(f"{name}: {len(ids)} entries -> {ids}")
        else:
            print(f"{name}: 1 entry")

if __name__ == "__main__":
    asyncio.run(main())
