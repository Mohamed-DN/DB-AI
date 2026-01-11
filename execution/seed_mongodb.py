"""
Seed MongoDB with required collections and sample data.
Matches the schema defined in MongoDB/struttura_mongo/collections/
"""
import os
import sys
from datetime import datetime
from pymongo import MongoClient

# Configuration
MONGO_HOST = os.getenv("MONGODB_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGODB_PORT", 28017))
MONGO_USER = os.getenv("MONGO_USERNAME", "admin")
MONGO_PASS = os.getenv("MONGO_PASSWORD", "nexi2024")
MONGO_DB = os.getenv("MONGODB_DB", "nexi_cmdb_v2")

print(f"Connecting to MongoDB at {MONGO_HOST}:{MONGO_PORT}...")

try:
    client = MongoClient(
        host=MONGO_HOST,
        port=MONGO_PORT,
        username=MONGO_USER,
        password=MONGO_PASS,
        serverSelectionTimeoutMS=5000
    )
    db = client[MONGO_DB]
    print(f"✅ Connected to {MONGO_DB}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

# --- SEED DATA ---

# 1. system_config - Agent intervals and global settings
system_config_docs = [
    {"key": "global_status", "value": "RUNNING", "updated_at": datetime.now()},
    {"key": "scout_interval", "value": 60, "updated_at": datetime.now()},
    {"key": "collector_interval", "value": 120, "updated_at": datetime.now()},
    {"key": "watcher_interval", "value": 30, "updated_at": datetime.now()},
    {"key": "criticalalert_interval", "value": 60, "updated_at": datetime.now()},
    {"key": "checkmk_bridge_interval", "value": 300, "updated_at": datetime.now()},
]

# 2. gateways - SSH gateways for database access
gateways_docs = [
    {
        "_id": "nexi-gw-milano2",
        "location": {"country": "Italy", "city": "Milan", "datacenter": "Docker Lab"},
        "info": {"hostname": "gw-milano2.nexi.lab", "ip_address": "172.21.1.1", "os_version": "Alpine Linux"},
        "network": {"open_ports": [22], "status": "UP"},
        "reachability": {"accessible_dbs": ["nexi-pg-milano-prod2", "nexi-pg-milano-dev2", "nexi-pg-milano-stg2"]},
        "ssh_config": {"user": "admin", "auth_method": "PASSWORD"},
        "created_at": datetime.now()
    },
    {
        "_id": "nexi-gw-bratislava2",
        "location": {"country": "Slovakia", "city": "Bratislava", "datacenter": "Docker Lab"},
        "info": {"hostname": "gw-bratislava2.nexi.lab", "ip_address": "172.21.2.1"},
        "network": {"open_ports": [22], "status": "UP"},
        "reachability": {"accessible_dbs": ["nexi-pg-bratislava-prod2", "nexi-pg-bratislava-dev2"]},
        "ssh_config": {"user": "admin", "auth_method": "PASSWORD"},
        "created_at": datetime.now()
    },
    {
        "_id": "nexi-gw-cairo2",
        "location": {"country": "Egypt", "city": "Cairo", "datacenter": "Docker Lab"},
        "info": {"hostname": "gw-cairo2.nexi.lab", "ip_address": "172.21.3.1"},
        "network": {"open_ports": [22], "status": "UP"},
        "reachability": {"accessible_dbs": ["nexi-oracle-cairo-primary2", "nexi-oracle-cairo-replica2"]},
        "ssh_config": {"user": "admin", "auth_method": "PASSWORD"},
        "created_at": datetime.now()
    }
]

# 3. business_services - Example service mapping
business_services_docs = [
    {
        "service_info": {
            "name": "Payments Platform",
            "service_now_id": "SN_APP_00001",
            "status": "ACTIVE",
            "criticality": "HIGH",
            "business_unit": "Digital Payments"
        },
        "contacts": {
            "bao": {"name": "DBA Team", "email": "dba@nexi.it"},
            "dl_team": "dl_payments_ops@nexi.it"
        },
        "technical_mapping": [
            {"db_unique_name": "NEXI-PG-MILANO-PROD2", "gateway_ref": "nexi-gw-milano2"}
        ],
        "compliance": {"data_classification": "CONFIDENTIAL", "gdpr_relevant": True, "pci_dss_scope": True},
        "created_at": datetime.now()
    }
]

# 4. Empty collections with indexes
empty_collections = [
    "discovery_queue",
    "agent_runs",
    "baselines",
    "compliance_reports",
    "rag_knowledge_base"
]

# --- INSERT DATA ---

def seed_collection(name, docs):
    coll = db[name]
    if coll.count_documents({}) > 0:
        print(f"⏭️  {name}: Already has data, skipping")
        return
    result = coll.insert_many(docs)
    print(f"✅ {name}: Inserted {len(result.inserted_ids)} documents")

def ensure_collection(name):
    if name not in db.list_collection_names():
        db.create_collection(name)
        print(f"✅ {name}: Created empty collection")
    else:
        print(f"⏭️  {name}: Already exists")

# Seed
seed_collection("system_config", system_config_docs)
seed_collection("gateways", gateways_docs)
seed_collection("business_services", business_services_docs)

for coll_name in empty_collections:
    ensure_collection(coll_name)

# --- VERIFY ---
print("\n📊 Final Collection List:")
for name in sorted(db.list_collection_names()):
    count = db[name].count_documents({})
    print(f"   - {name}: {count} docs")

print("\n🎉 Seed complete!")
