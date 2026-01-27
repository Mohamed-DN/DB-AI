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

# 4. inventory_databases - The core database inventory (HIERARCHICAL FORMAT)
# Following the Oracle/PostgreSQL templates defined in mongo/schemas/json/templates/

def build_postgres_doc(container_name, port, environment, role, gateway="nexi-gw-milano2"):
    """Build a full hierarchical PostgreSQL document"""
    return {
        "metadata": {
            "extraction_timestamp": datetime.now().isoformat(),
            "agent_version": "2.0.0",
            "db_technology": "POSTGRESQL",
            "environment": environment
        },
        "cluster_identity": {
            "system_identifier": None,
            "timeline_id": None,
            "cluster_name": container_name,
            "version_major": 15,
            "version_full": "PostgreSQL 15.x",
            "uptime_seconds": None
        },
        "instance_details": {
            "role": role,
            "inet_server_addr": "127.0.0.1",
            "inet_server_port": port,
            "is_in_recovery": False if role == "PRIMARY" else None
        },
        "resource_config": {
            "connections": {"max_connections": 500 if "prod" in container_name.lower() else 100, "current_active": None},
            "memory": {"shared_buffers": None, "effective_cache_size": None, "work_mem": None, "maintenance_work_mem": None},
            "wal": {"wal_level": None, "max_wal_size": None}
        },
        "replication_ha": {
            "manager": None,
            "sync_standby_names": None,
            "replication_slots": []
        },
        "storage_info": {
            "database_size_bytes": None,
            "temp_file_limit": None,
            "tablespaces": []
        },
        "extensions_installed": [],
        # Backward compatibility fields
        "identity": {
            "db_unique_name": container_name.upper().replace("-", "_"),
            "db_name": container_name,
            "family": "POSTGRESQL",
            "engine": "POSTGRES",
            "role": role,
            "environment": environment,
            "host": "127.0.0.1",
            "gateway_ref": gateway
        },
        "connection": {
            "port": port,
            "container": container_name,
            "type": "DOCKER"
        },
        "state": {
            "status": "UP",
            "last_seen": datetime.now().isoformat()
        },
        "created_at": datetime.now()
    }

def build_oracle_doc(container_name, port, environment, role, gateway="nexi-gw-cairo2"):
    """Build a full hierarchical Oracle document"""
    return {
        "metadata": {
            "extraction_timestamp": datetime.now().isoformat(),
            "agent_version": "2.0.0",
            "db_technology": "ORACLE",
            "environment": environment
        },
        "infrastructure": {
            "host": {
                "alias": container_name,
                "ip_address": "127.0.0.1",
                "os": "OracleLinux",
                "cloud_provider": "Docker",
                "tenant": "NEXI"
            },
            "hardware": {
                "type": "Docker Container",
                "resources": {"cpu_sockets": 1, "cores": 4, "ram_gb": 8}
            }
        },
        "database_core": {
            "identity": {
                "dbid": None,
                "db_name": container_name.split("-")[-1] if "-" in container_name else container_name,
                "db_unique_name": container_name.upper().replace("-", "_"),
                "service_name": "ORCL",
                "instance_name": None
            },
            "version_info": {
                "full_version": "19.x",
                "patch_level": None,
                "compatibility": "19.0.0"
            },
            "configuration": {
                "type": "NON-CDB",
                "pdb_status": None,
                "charset": "AL32UTF8",
                "performance_mode": "MAXIMUM PERFORMANCE"
            }
        },
        "network": {
            "listeners": [{"port": port, "protocol": "TCP"}],
            "cluster_interconnect": {
                "scan_name": None,
                "scan_ips": [],
                "node_vips": []
            }
        },
        "ha_dr": {
            "cluster_roles": ["HAS"] if role == "PRIMARY" else [],
            "dataguard": {
                "role": role,
                "target": "nexi-oracle-cairo-replica2" if role == "PRIMARY" else "nexi-oracle-cairo-primary2",
                "transport_type": "ASYNC"
            }
        },
        # Backward compatibility fields
        "identity": {
            "db_unique_name": container_name.upper().replace("-", "_"),
            "db_name": container_name,
            "family": "ORACLE",
            "engine": "ORACLE",
            "role": role,
            "environment": environment,
            "host": "127.0.0.1",
            "gateway_ref": gateway
        },
        "connection": {
            "port": port,
            "container": container_name,
            "service_name": "ORCL",
            "type": "DOCKER"
        },
        "state": {
            "status": "UP",
            "last_seen": datetime.now().isoformat()
        },
        "created_at": datetime.now()
    }

def build_nosql_doc(container_name, port, engine, environment="INFRASTRUCTURE"):
    """Build a document for NoSQL databases"""
    return {
        "metadata": {
            "extraction_timestamp": datetime.now().isoformat(),
            "agent_version": "2.0.0",
            "db_technology": engine.upper(),
            "environment": environment
        },
        "identity": {
            "db_unique_name": container_name.upper().replace("-", "_"),
            "db_name": container_name,
            "family": engine.upper(),
            "engine": engine.upper(),
            "role": "PRIMARY",
            "environment": environment,
            "host": "127.0.0.1"
        },
        "connection": {
            "port": port,
            "container": container_name,
            "type": "DOCKER"
        },
        "state": {
            "status": "UP",
            "last_seen": datetime.now().isoformat()
        },
        "created_at": datetime.now()
    }

# Generate hierarchical documents
inventory_databases_docs = [
    # PostgreSQL Instances
    build_postgres_doc("nexi-pg-milano-prod2", 5432, "PRODUCTION", "PRIMARY"),
    build_postgres_doc("nexi-pg-milano-dev2", 5433, "DEVELOPMENT", "DEV"),
    build_postgres_doc("nexi-pg-milano-stg2", 5434, "STAGING", "STAGING"),
    build_postgres_doc("nexi-pg-bratislava-prod2", 5437, "PRODUCTION", "PRIMARY", "nexi-gw-bratislava2"),
    build_postgres_doc("nexi-pg-bratislava-dev2", 5438, "DEVELOPMENT", "DEV", "nexi-gw-bratislava2"),
    # Oracle Instances
    build_oracle_doc("nexi-oracle-cairo-primary2", 1521, "PRODUCTION", "PRIMARY"),
    build_oracle_doc("nexi-oracle-cairo-replica2", 1522, "DISASTER_RECOVERY", "REPLICA"),
    # NoSQL Instances
    build_nosql_doc("nexi-mongodb2", 28017, "MONGODB"),
    build_nosql_doc("nexi-redis2", 7379, "REDIS"),
    build_nosql_doc("nexi-qdrant2", 6333, "QDRANT", "AI_INFRASTRUCTURE"),
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
