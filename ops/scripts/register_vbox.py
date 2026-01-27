import pymongo
from datetime import datetime

# Connect
client = pymongo.MongoClient("mongodb://admin:nexi2024@localhost:28017/?authSource=admin")
db = client["nexi_cmdb_v2"]

# 1. Register Tunneled OEM
inst = {
    "name": "VirtualBox Enterprise OEM",
    "url": "https://localhost:7803/em",
    "username": "sysman",
    "password": "root", # As provided by user
    "verify_ssl": False,
    "is_connected": True,
    "last_check": datetime.utcnow()
}
db.oem_instances.update_one({"name": inst["name"]}, {"$set": inst}, upsert=True)
print(f"Registered OEM: {inst['name']}")

# 2. Register Tunneled Database Target (Primary)
target = {
    "identity": {"db_unique_name": "VBOX_CDB", "engine": "ORACLE"},
    "state": {"status": "UP"},
    "connection": {"host": "localhost", "port": 1521},
    "oem_metrics": {
         # Initialize with empty metrics so it appears in list, collector will fill real values
        "cpu_usage_percent": 0,
        "active_sessions": 0
    },
    "oem_last_collected": datetime.utcnow()
}
db.databases.update_one({"identity.db_unique_name": "VBOX_CDB"}, {"$set": target}, upsert=True)
print("Registered Database: VBOX_CDB")
print("Done!")
