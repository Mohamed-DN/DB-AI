"""Update MongoDB with correct Oracle configuration"""
from pymongo import MongoClient
from datetime import datetime

MONGO_URI = "mongodb://admin:pippopippo_1234@localhost:28017/"
MONGO_DB = "m-dn_cmdb_v2"

updates = [
    {
        "_id": "ORACLE_VM1_DEV",
        "identity.service_name": "FREEPDB1",
        "identity.sid": "",  # Clear SID, use service_name instead
        "identity.port": 2521,
        "connection_info.monitoring_user": "system",
        "connection_info.monitoring_password": "root"
    },
    {
        "_id": "ORACLE_VM2_DEV",
        "identity.service_name": "FREEPDB1",
        "identity.sid": "",
        "identity.port": 2522,
        "connection_info.monitoring_user": "system",
        "connection_info.monitoring_password": "root"
    }
]

print("📝 Updating MongoDB with correct Oracle configuration...")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

for update in updates:
    vm_id = update.pop("_id")
    db.inventory_databases.update_one(
        {"_id": vm_id},
        {"$set": update}
    )
    print(f"  ✅ Updated {vm_id}: service_name=FREEPDB1, password=root")

client.close()
print("\n✅ Configuration updated!")
print("   Test with: python ops/scripts/oem_scraper.py --discover-from-mongo --once")
