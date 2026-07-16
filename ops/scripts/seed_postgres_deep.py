import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load V2 Env
env_path = os.path.join(os.path.dirname(__file__), '../.env.v2')
load_dotenv(env_path)

MONGO_URI = f"mongodb://{os.getenv('MONGO_USERNAME', 'admin')}:{os.getenv('MONGO_PASSWORD', 'password')}@localhost:{os.getenv('MONGODB_PORT', '28017')}"
DB_NAME = os.getenv('MONGODB_DB', 'm-dn_cmdb_v2')

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db['inventory_databases']

# Demo Data - PostgreSQL Enterprise Deep Dive (Verified Schema)
# Simulating a high-traffic Payment Core database under Patroni
demo_db = {
    "identity": {
        "db_name": "pg-payment-core-prod",
        "db_unique_name": "pg-payment-core-prod",
        "service_name": "payment-core-01",
        "dbid": "system_732891029384",
        "engine": "POSTGRESQL",
        "host": "m-dn-pg-milano-prod",
        "environment": "PROD"
    },
    "connection": {
        "type": "DOCKER",
        "container": "m-dn-pg-milano-prod",
        "port": 5432
    },
    "infrastructure": {
        "provider": "ON_PREM_DC_MILANO",
        "region": "MILANO_ZO_1",
        "os": "Red Hat Enterprise Linux 8.9",
        "hardware": "Bare Metal (CPU: 32, RAM: 256GB)"
    },
    "instance_details": {
        "role": "LEADER",
        "state": "running",
        "version": "15.4 (Enterprise)",
        "uptime_seconds": 1209600,
        "connections": {
            "max": 500,
            "used": 342,
            "reserved_super": 5
        },
        "archiver": {
            "archived_count": 89012,
            "last_archived_time": "2024-01-15T10:00:00Z",
            "failed_count": 0,
            "last_failed_time": None
        }
    },
    "deep_configuration": {
        "memory": {
            "shared_buffers": "64GB",
            "effective_cache_size": "190GB",
            "work_mem": "128MB",
            "maintenance_work_mem": "4GB"
        },
        "wal_tuning": {
            "wal_level": "logical",
            "max_wal_size": "16GB",
            "min_wal_size": "2GB",
            "checkpoint_timeout": "30min"
        },
        "autovacuum": {
            "autovacuum": "on",
            "autovacuum_max_workers": 5
        }
    },
    "replication": {
        "sync_standby_names": "pg-payment-core-02,pg-payment-core-03",
        "replication_slots": [
            {
                "slot_name": "standby_node_2",
                "plugin": "physical",
                "slot_type": "physical",
                "active": True,
                "restart_lsn": "0/18000060",
                "calculated_lag_bytes": 0
            },
            {
                "slot_name": "debezium_cdc_kafka_connect",
                "plugin": "wal2json",
                "slot_type": "logical",
                "active": True,
                "restart_lsn": "0/18000990",
                "calculated_lag_bytes": 1024
            }
        ],
        "peers": [
            {
                "client_addr": "10.20.40.56",
                "state": "streaming",
                "sync_state": "sync",
                "application_name": "pg-payment-core-02",
                "sent_lsn": "0/18000060",
                "write_lsn": "0/18000060",
                "flush_lsn": "0/18000060",
                "replay_lsn": "0/18000060",
                "write_lag": "0s",
                "flush_lag": "0s",
                "replay_lag": "1ms"
            },
               {
                "client_addr": "10.20.40.57",
                "state": "streaming",
                "sync_state": "async",
                "application_name": "pg-payment-core-03",
                "sent_lsn": "0/18000090",
                "write_lsn": "0/18000090",
                "flush_lsn": "0/18000080",
                "replay_lsn": "0/18000080",
                "write_lag": "10ms",
                "flush_lag": "20ms",
                "replay_lag": "45ms"
            }
        ]
    },
    "storage_deep_dive": {
        "database_size_bytes": 2450000000000,
        "database_size_human": "2.2 TB",
        "wal_dir_size_bytes": 8589934592,
        "tablespaces": [
            {
                "spcname": "pg_default",
                "path": "base/16384",
                "size_human": "150 GB"
            },
            {
                "spcname": "ts_payments_high_performance_ssd",
                "path": "/mnt/nvme_ssd_raid10/data",
                "size_human": "2 TB"
            }
        ]
    }
}

# Upsert based on unique name
result = collection.update_one(
    {"identity.db_unique_name": demo_db["identity"]["db_unique_name"]},
    {"$set": demo_db},
    upsert=True
)

print(f"✅ Deep PostgreSQL Database Seeded: {demo_db['identity']['db_name']}")
if result.upserted_id:
    print(f"   Created new document with ID: {result.upserted_id}")
else:
    print("   Updated existing document.")
