import pymongo
from datetime import datetime
import os

# Connect to MongoDB (using default or env var)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:nexi2024@localhost:28017/?authSource=admin")
client = pymongo.MongoClient(MONGO_URI)
db = client["nexi_cmdb_v2"]

instance = {
    "name": "OEM Docker Beast",
    "url": "https://oemserver:7802/em", # Internal Docker network hostname
    "username": "sysman",
    "password": "password123", # From our install script
    "verify_ssl": False,
    "is_connected": True,
    "created_at": datetime.utcnow()
}

# Update or Insert
db.oem_instances.update_one(
    {"name": instance["name"]},
    {"$set": instance},
    upsert=True
)

print(f"Registered OEM Instance: {instance['name']}")
print("Current Instances:")
for doc in db.oem_instances.find():
    print(f"- {doc['name']} ({doc['url']})")
