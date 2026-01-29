import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MIN_URI = "mongodb://localhost:27017/"

async def list_dbs():
    print(f"Connecting to {MIN_URI}...")
    client = AsyncIOMotorClient(MIN_URI)
    
    try:
        dbs = await client.list_database_names()
        print(f"Found Databases: {dbs}")
        
        for db_name in dbs:
            if db_name in ['admin', 'local', 'config']:
                continue
                
            print(f"\n--- Analysis of DB: '{db_name}' ---")
            db = client[db_name]
            collections = await db.list_collection_names()
            
            total_docs = 0
            for col_name in collections:
                count = await db[col_name].count_documents({})
                print(f"  - {col_name}: {count} docs")
                total_docs += count
            
            print(f"  [TOTAL] {db_name}: {total_docs} documents")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(list_dbs())
