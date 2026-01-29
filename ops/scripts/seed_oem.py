import pymongo
from datetime import datetime

# Connect
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["nexi_cmdb_v2"]

# 1. Seed Instance
instance = {
    "name": "OEM Production",
    "url": "https://oem.nexi.lab:7803/em",
    "username": "sysman",
    "is_connected": True,
    "last_check": datetime.utcnow()
}
db.oem_instances.update_one({"name": instance["name"]}, {"$set": instance}, upsert=True)
print("Seeded OEM Instance")

# 2. Seed Database Target
metrics = {
    "cpu_usage_percent": 12.5,
    "memory_usage_percent": 45.2,
    "active_sessions": 8,
    "wait_time_ratio": 0.05,
    "response_time": 4.2,
    "tablespace_used_pct": 78.5,
    "io_throughput": 125.0,
    "redo_log_switches": 12,
    "buffer_cache_hit_ratio": 99.8,
    "shared_pool_free_pct": 15.2
}

target = {
    "identity": {"db_unique_name": "JUPITER", "engine": "ORACLE"},
    "state": {"status": "UP"},
    "connection": {"host": "oracle-cairo-primary2.nexi.lab", "port": 1521},
    "oem_metrics": metrics,
    "oem_last_collected": datetime.utcnow()
}

db.databases.update_one(
    {"identity.db_unique_name": "JUPITER"},
    {"$set": target},
    upsert=True
)
print("Seeded JUPITER Database")

# 3. Seed PDB Targets
pdb_metrics = metrics.copy()
pdb_metrics["cpu_usage_percent"] = 5.2 # Lower CPU for PDB

pdb1 = {
    "identity": {"db_unique_name": "JUPITER_PDB1", "engine": "ORACLE"},
    "state": {"status": "OPEN"},
    "connection": {"host": "oracle-cairo-primary2.nexi.lab", "port": 1521},
    "oem_metrics": pdb_metrics,
    "oem_last_collected": datetime.utcnow()
}

db.databases.update_one(
    {"identity.db_unique_name": "JUPITER_PDB1"},
    {"$set": pdb1},
    upsert=True
)
print("Seeded JUPITER_PDB1")

print("Done!")
