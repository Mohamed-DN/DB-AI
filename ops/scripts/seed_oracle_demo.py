import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Load V2 Env
env_path = os.path.join(os.path.dirname(__file__), '../.env.v2')
load_dotenv(env_path)

MONGO_URI = f"mongodb://{os.getenv('MONGO_USERNAME', 'admin')}:{os.getenv('MONGO_PASSWORD', 'password')}@localhost:{os.getenv('MONGODB_PORT', '28017')}"
DB_NAME = os.getenv('MONGODB_DB', 'nexi_cmdb_v2')

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db['inventory_databases']

# Demo Data - Oracle RAC (Hybrid of User Request + Backend Compatibility)
demo_db = {
    "identity": {
        "db_name": "PAUNRTODSI",
        "db_unique_name": "PAUNRTODSI", # Using name as unique name for simplicity or mapping
        "service_name": "UNRTODSI_PRY",
        "dbid": "242.648.470",
        "engine": "ORACLE",
        "host": "maamdba2ucrti01",
        "environment": "INTEGRATION"
    },
    "connection": {
        "type": "DOCKER", # Makes main.py try to exec into a container
        "container": "nexi-oracle-cairo-primary", # Maps to actual docker container for terminal access
        "port": 1521
    },
    "status": {
        "status": "UP",
        "active_sessions": 42,
        "idle_sessions": 120
    },
    "infrastructure": {
        "provider": "AZURE",
        "region": "West Europe",
        "os": "OracleLinux 8.10",
        "hardware": "VM (4 Core, 62GB RAM)"
    },
    "network": {
         "scan_name": "scan-prod-cluster",
         "scan_ips": ["10.158.133.20", "10.158.133.21", "10.158.133.22"],
         "vip_ips": ["10.158.133.30", "10.158.133.31"],
         "vip_names": ["maamdba2ucrti01-vip", "maamdba2ucrti02-vip"]
    },
    "ha_dr": {
        "architecture": "RAC",
        "nodes": 2,
        "cli_status": {
            "crsctl_output": "CRS-4638: Oracle High Availability Services is online",
            "srvctl_status": "Instance PAUNRTODSI1 is running on node maamdba2ucrti01.\nInstance PAUNRTODSI2 is running on node maamdba2ucrti02.\nDatabase role: PRIMARY",
            "derived_role": "PRIMARY"
        },
        "dataguard": {
            "status": "PROTECTION MODE: MAXPERFORMANCE",
            "database_role": "PRIMARY",
            "switchover_status": "TO STANDBY",
            "lag_metrics": {
                "transport_lag": "+00 00:00:00",
                "apply_lag": "+00 00:00:00"
            }
        },
        "goldengate": {
            "present": True,
            "status": "RUNNING",
            "capture_name": "E_ORA",
            "lag_seconds": 1
        }
    },
    "storage": {
        "total_size": "1.2 TB",
        "total_size_bytes": 1319413953331,
        "disk_groups": [
            {"name": "DATA", "state": "MOUNTED", "type": "EXTERN", "total_mb": 2048000, "free_mb": 450000},
            {"name": "RECO", "state": "MOUNTED", "type": "EXTERN", "total_mb": 1024000, "free_mb": 800000},
            {"name": "OCR_VOTE", "state": "MOUNTED", "type": "NORMAL", "total_mb": 51200, "free_mb": 49000}
        ],
        "tablespaces": [
             {"name": "SYSTEM", "used_pct": 85, "used_gb": 12, "max_gb": 20},
             {"name": "USERS", "used_pct": 45, "used_gb": 150, "max_gb": 500},
             {"name": "DATA_APP", "used_pct": 72, "used_gb": 600, "max_gb": 800}
        ]
    }
}

# Upsert based on unique name
result = collection.update_one(
    {"identity.db_unique_name": demo_db["identity"]["db_unique_name"]},
    {"$set": demo_db},
    upsert=True
)

print(f"✅ Demo Database Seeded: {demo_db['identity']['db_name']}")
if result.upserted_id:
    print(f"   Created new document with ID: {result.upserted_id}")
else:
    print("   Updated existing document.")
