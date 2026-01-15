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

# 4. inventory_databases - The core database inventory
inventory_databases_docs = [
    # PostgreSQL Instances
    {
        "identity": {"db_unique_name": "NEXI-PG-MILANO-PROD2", "family": "POSTGRESQL", "engine": "POSTGRES", "role": "PRIMARY", "environment": "PRODUCTION", "host": "127.0.0.1"},
        "connection": {"port": 5432, "max_connections": 500, "container": "nexi-pg-milano-prod2"},
        "business_service_ref": "Payments Platform",
        "created_at": datetime.now()
    },
    {
        "identity": {"db_unique_name": "NEXI-PG-MILANO-DEV2", "family": "POSTGRESQL", "engine": "POSTGRES", "role": "DEV", "environment": "DEVELOPMENT", "host": "127.0.0.1"},
        "connection": {"port": 5433, "max_connections": 100, "container": "nexi-pg-milano-dev2"},
        "created_at": datetime.now()
    },
    {
        "identity": {"db_unique_name": "NEXI-PG-MILANO-STG2", "family": "POSTGRESQL", "engine": "POSTGRES", "role": "STAGING", "environment": "STAGING", "host": "127.0.0.1"},
        "connection": {"port": 5434, "max_connections": 200, "container": "nexi-pg-milano-stg2"},
        "created_at": datetime.now()
    },
    {
        "identity": {"db_unique_name": "NEXI-PG-BRATISLAVA-PROD2", "family": "POSTGRESQL", "engine": "POSTGRES", "role": "PRIMARY", "environment": "PRODUCTION", "host": "127.0.0.1"},
        "connection": {"port": 5437, "container": "nexi-pg-bratislava-prod2"},
        "created_at": datetime.now()
    },
    {
        "identity": {"db_unique_name": "NEXI-PG-BRATISLAVA-DEV2", "family": "POSTGRESQL", "engine": "POSTGRES", "role": "DEV", "environment": "DEVELOPMENT", "host": "127.0.0.1"},
        "connection": {"port": 5438, "container": "nexi-pg-bratislava-dev2"},
        "created_at": datetime.now()
    },
    # Oracle Instances
    {
        "identity": {"db_unique_name": "NEXI-ORACLE-CAIRO-PRIMARY2", "family": "ORACLE", "engine": "ORACLE", "role": "PRIMARY", "environment": "PRODUCTION", "host": "127.0.0.1"},
        "connection": {"port": 1521, "service_name": "ORCL", "container": "nexi-oracle-cairo-primary2"},
        "created_at": datetime.now()
    },
    {
        "identity": {"db_unique_name": "NEXI-ORACLE-CAIRO-REPLICA2", "family": "ORACLE", "engine": "ORACLE", "role": "REPLICA", "environment": "DISASTER_RECOVERY", "host": "127.0.0.1"},
        "connection": {"port": 1522, "service_name": "ORCL", "container": "nexi-oracle-cairo-replica2"},
        "created_at": datetime.now()
    },
    # NoSQL Instances
    {
        "identity": {"db_unique_name": "NEXI-MONGODB2", "family": "MONGODB", "engine": "MONGODB", "role": "PRIMARY", "environment": "INFRASTRUCTURE", "host": "127.0.0.1"},
        "connection": {"port": 27017, "container": "nexi-mongodb2"},
        "created_at": datetime.now()
    },
    {
        "identity": {"db_unique_name": "NEXI-REDIS2", "family": "REDIS", "engine": "REDIS", "role": "PRIMARY", "environment": "INFRASTRUCTURE", "host": "127.0.0.1"},
        "connection": {"port": 6379, "container": "nexi-redis2"},
        "created_at": datetime.now()
    },
    {
        "identity": {"db_unique_name": "NEXI-QDRANT2", "family": "VECTOR", "engine": "QDRANT", "role": "PRIMARY", "environment": "AI_INFRASTRUCTURE", "host": "127.0.0.1"},
        "connection": {"port": 6333, "container": "nexi-qdrant2"},
        "created_at": datetime.now()
    }
]

# 5. Guide Templates - JSON Schemas for Users
guide_templates_docs = [
    {
        "_id": "template_database_inventory",
        "title": "Database Inventory Template",
        "description": "Schema for adding new databases to 'inventory_databases' collection",
        "template": {
            "identity": {
                "db_unique_name": "UNIQUE_IDENTIFIER_UPPERCASE",
                "family": "POSTGRESQL|ORACLE|MONGODB|REDIS|MYSQL",
                "engine": "Specific version or engine subtype",
                "role": "PRIMARY|REPLICA|STANDBY|DEV",
                "environment": "PRODUCTION|STAGING|DEVELOPMENT",
                "host": "IP address or hostname"
            },
            "connection": {
                "port": 5432,
                "schema": "public",
                "service_name": "ORCL (for Oracle)",
                "container": "docker-container-name (if applicable)"
            },
            "configuration": {
                "ha_enabled": False,
                "dr_enabled": False
            }
        },
        "required_fields": ["identity.db_unique_name", "identity.host", "identity.engine"],
        "example": {
            "identity": {"db_unique_name": "NEXI-PG-ROME-01", "family": "POSTGRESQL", "engine": "POSTGRES", "role": "PRIMARY", "environment": "PRODUCTION", "host": "10.0.0.50"},
            "connection": {"port": 5432, "schema": "payments"}
        }
    },
    {
        "_id": "template_monitoring_alert",
        "title": "Monitoring Alert Template",
        "description": "Structure for alerts inserted by agents into 'monitoring_alerts'",
        "template": {
            "severity": "CRITICAL|WARNING|INFO",
            "type": "DATABASE_DOWN|HIGH_CPU|STORAGE_FULL|SLOW_QUERY",
            "message": "Human readable description",
            "database": "DB_UNIQUE_NAME reference",
            "timestamp": "ISO Date",
            "processed": False,
            "state": "OPEN|ACKNOWLEDGED|RESOLVED"
        }
    }
]

# 6. Empty collections with indexes
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
seed_collection("inventory_databases", inventory_databases_docs)
seed_collection("guide_templates", guide_templates_docs)

for coll_name in empty_collections:
    ensure_collection(coll_name)

# --- VERIFY ---
print("\n📊 Final Collection List:")
for name in sorted(db.list_collection_names()):
    count = db[name].count_documents({})
    print(f"   - {name}: {count} docs")

print("\n🎉 Seed complete!")
