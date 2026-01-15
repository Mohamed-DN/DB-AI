from pymongo import MongoClient
import datetime
import os
from dotenv import load_dotenv

# Load Environment
load_dotenv(dotenv_path='.env.v2')

# Connect to MongoDB
mongo_uri = f"mongodb://{os.getenv('MONGO_USERNAME')}:{os.getenv('MONGO_PASSWORD')}@localhost:{os.getenv('MONGODB_PORT', '28017')}/?authSource=admin"
client = MongoClient(mongo_uri)
db = client[os.getenv('MONGODB_DB', 'nexi_cmdb_v2')]
collection = db['inventory_databases']

# Demo Data: Oracle RAC Standby (Replica)
# Based on primary PAUNRTODSI
standby_db = {
    "identity": {
        "db_name": "PAUNRTODSI",
        "db_unique_name": "PAUNRTODSI_STBY", # Distinct for Inventory
        "service_name": "UNRTODSI_STBY",
        "dbid": "242.648.470", # Same DBID as Primary (Physical Standby)
        "engine": "ORACLE",
        "host": "maamdba2ucrti03", # Different host
        "environment": "INTEGRATION",
        "gateway_ref": "nexi-gw-cairo2"
    },
    "metadata_version": "2.1-deep",
    "cluster_identity": {
        "db_unique_name": "PAUNRTODSI_STBY",
        "dbid": "242.648.470",
        "platform_name": "Linux x86 64-bit",
        "version_full": "19.0.0.0.0",
        "database_role": "PHYSICAL STANDBY", # KEY DIFFERENCE
        "open_mode": "READ ONLY WITH APPLY" # Active Data Guard
    },
    "instances": [
        {
           "inst_id": 1,
           "instance_name": "PAUNRTODSI1",
           "host_name": "maamdba2ucrti03",
           "status": "OPEN",
           "database_status": "ACTIVE",
           "logins": "ALLOWED"
        },
        {
           "inst_id": 2,
           "instance_name": "PAUNRTODSI2",
           "host_name": "maamdba2ucrti04",
           "status": "OPEN",
           "database_status": "ACTIVE",
           "logins": "ALLOWED"
        }
    ],
    "connection": {
        "type": "REMOTE", # Simulated Remote
        "container": "nexi-oracle-cairo-replica2",
        "port": 1521
    },
    "ha_dr": {
        "architecture": "RAC",
        "nodes": 2,
        "cli_status": {
            "crsctl_output": "CRS-4638: Oracle High Availability Services is online",
            "srvctl_status": "Instance PAUNRTODSI1 is running on node maamdba2ucrti03.\nInstance PAUNRTODSI2 is running on node maamdba2ucrti04.\nDatabase role: PHYSICAL_STANDBY",
            "derived_role": "PHYSICAL STANDBY"
        },
        "dataguard": {
            "status": "PROTECTION MODE: MAXPERFORMANCE",
            "database_role": "PHYSICAL STANDBY",
            "switchover_status": "NOT ALLOWED", # Typical for standby
            "lag_metrics": {
                "transport_lag": "+00 00:00:00",
                "apply_lag": "+00 00:05:32" # Simulated Lag
            }
        },
        "goldengate": {
            "present": True,
            "status": "RUNNING",
            "process_type": "REPLICAT",
            "capture_name": "R_ORA_STBY",
            "lag_seconds": 15
        }
    },
    "infrastructure": {
        "provider": "AZURE",
        "region": "West Europe",
        "os": "OracleLinux 8.10",
        "hardware": "VM (4 Core, 62GB RAM)"
    },
    "network": {
        "scan_name": "scan-stby-cluster",
        "scan_ips": ["10.158.134.20", "10.158.134.21", "10.158.134.22"],
        "vip_ips": ["10.158.134.30", "10.158.134.31"],
        "vip_names": ["maamdba2ucrti03-vip", "maamdba2ucrti04-vip"]
    },
    "status": {
        "status": "UP",
        "active_sessions": 5, # Less load on standby
        "idle_sessions": 20
    },
    "storage": {
        "total_size": "1.2 TB",
        "total_size_bytes": 1319413953331,
        "disk_groups": [
            {"name": "DATA", "state": "MOUNTED", "type": "EXTERN", "total_mb": 2048000, "free_mb": 460000},
            {"name": "RECO", "state": "MOUNTED", "type": "EXTERN", "total_mb": 1024000, "free_mb": 810000},
            {"name": "OCR_VOTE", "state": "MOUNTED", "type": "NORMAL", "total_mb": 51200, "free_mb": 49000}
        ]
    },
    "state": {
        "last_seen": datetime.datetime.now(),
        "status": "UP"
    }
}

# Upsert
filter_query = {"identity.db_unique_name": standby_db["identity"]["db_unique_name"]}
update_query = {"$set": standby_db}
result = collection.update_one(filter_query, update_query, upsert=True)

print(f"✅ Standby Oracle Database Seeded: {standby_db['identity']['db_unique_name']}")
