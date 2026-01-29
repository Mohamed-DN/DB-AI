
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def dump():
    uri = "mongodb://admin:nexi2024@127.0.0.1:28017/?authSource=admin"
    client = AsyncIOMotorClient(uri)
    db = client['nexi_cmdb_v2']
    docs = await db['oem_instances'].find().to_list(100)
    print(f"DEBUG: Found {len(docs)} docs")
    for d in docs:
        print(f" - {d.get('name')}: {d.get('url')}")

if __name__ == "__main__":
    asyncio.run(dump())
