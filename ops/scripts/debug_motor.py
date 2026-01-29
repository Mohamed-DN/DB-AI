
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def test_motor():
    # Use same settings as .env
    host = "localhost"
    port = 28017
    user = "admin"
    password = "nexi2024"
    db_name = "nexi_cmdb_v2"
    
    uri = f"mongodb://{user}:{password}@{host}:{port}/?authSource=admin"
    print(f"🔌 Connecting to {uri}...")
    
    try:
        client = AsyncIOMotorClient(uri)
        # Force connection verification
        await client.admin.command('ping')
        print("✅ Ping successful!")
        
        db = client[db_name]
        count = await db.oem_instances.count_documents({})
        print(f"📊 OEM Count (Async): {count}")
        
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_motor())
