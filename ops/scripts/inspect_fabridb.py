import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json

URI = "mongodb://localhost:27017/"
DB = "fabridb"
COL = "cmdb"

async def inspect():
    client = AsyncIOMotorClient(URI)
    db = client[DB]
    doc = await db[COL].find_one()
    
    if doc:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        print(json.dumps(doc, indent=2,  default=str))
    else:
        print("No document found in fabridb.cmdb")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(inspect())
