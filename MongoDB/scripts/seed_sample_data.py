"""
Seed sample data for testing
"""
import sys
from datetime import datetime, timedelta
sys.path.append('..')

from src.connection import get_database


def seed_sample_data():
    """Insert sample data for testing"""
    db = get_database()

    # Sample inventory_databases
    print("Inserting sample databases...")
    sample_dbs = [
        {
            "identity": {
                "db_unique_name": "NZSEP",
                "db_name": "DBRBNZP",
                "engine": "ORACLE",
                "topology": "RAC",
                "environment": "PROD",
                "gateway_ref": "dbgec2"
            },
            "nodes": [
                {
                    "node_name": "NZSEP1",
                    "hostname": "ldbrbnzp03.gpaprod.local",
                    "host_ip": "10.102.161.51",
                    "role": "PRIMARY",
                    "status": "OPEN",
                    "host_specs": {
                        "os": {"distro": "Red Hat Enterprise Linux", "version": "8.6", "kernel": "4.18.0"},
                        "cpu": {"model": "Intel Xeon Gold", "architecture": "x86_64", "sockets": 2, "cores_per_socket": 24, "threads_total": 96},
                        "memory": {"total_gb": 512, "hugepages_configured": True, "hugepages_size_gb": 256}
                    }
                }
            ],
            "configuration": {
                "version": "19.16.0.0",
                "port": 1521,
                "oracle_home": "/u01/app/oracle/product/19.0.0/dbhome_1",
                "patches": ["35042068", "35050341"]
            },
            "licensing": {
                "product_edition": "ENTERPRISE",
                "active_options": ["RAC", "PARTITIONING", "DIAGNOSTICS_PACK"]
            },
            "storage": {
                "last_check": datetime.utcnow(),
                "asm_diskgroups": [
                    {"name": "DATA", "total_gb": 2048, "max_gb": 3000, "used_pct": 80, "alert_threshold_pct": 90, "state": "MOUNTED"},
                    {"name": "RECO", "total_gb": 1024, "max_gb": 1500, "used_pct": 30, "alert_threshold_pct": 90, "state": "MOUNTED"}
                ],
                "tablespaces": [
                    {"name": "SYSTEM", "used_pct": 89, "autoextensible": "YES", "alert_threshold_pct": 90},
                    {"name": "APP_DATA", "used_pct": 92, "autoextensible": "NO", "max_gb": 500, "alert_threshold_pct": 90}
                ]
            },
            "policies": {
                "data_retention": {"enabled": True, "retention_days": 365, "partition_manager": True}
            }
        },
        {
            "identity": {
                "db_unique_name": "PGPROD01",
                "db_name": "payments_db",
                "engine": "POSTGRES",
                "topology": "REPLICA_SET",
                "environment": "PROD",
                "gateway_ref": "dbgec2"
            },
            "nodes": [
                {
                    "node_name": "pgprod01-primary",
                    "hostname": "pgprod01.nexi.local",
                    "host_ip": "10.102.170.10",
                    "role": "PRIMARY",
                    "status": "OPEN"
                }
            ],
            "configuration": {
                "version": "15.4",
                "port": 5432
            },
            "licensing": {
                "product_edition": "COMMUNITY",
                "active_options": []
            }
        }
    ]

    for db_doc in sample_dbs:
        db.inventory_databases.update_one(
            {"identity.db_unique_name": db_doc["identity"]["db_unique_name"]},
            {"$set": db_doc},
            upsert=True
        )

    # Sample business_services
    print("Inserting sample services...")
    sample_services = [
        {
            "service_info": {
                "name": "Gestione Carte di Credito",
                "service_now_id": "SN_APP_00912",
                "status": "ACTIVE"
            },
            "contacts": {
                "bao": {"name": "Mario Rossi", "email": "mario.rossi@nexi.it"},
                "dl_team": "dl_carte_ops@nexi.it",
                "reperibilita_number": "+39 335 9988776",
                "snow_group": "DBA-Oracle-Prod"
            },
            "technical_mapping": [
                {
                    "db_unique_name": "NZSEP",
                    "schemas": [
                        {"schema_name": "CRD_OWNER", "type": "OWNER"},
                        {"schema_name": "CRD_APP_USER", "type": "USER"}
                    ]
                }
            ]
        }
    ]

    for svc in sample_services:
        db.business_services.update_one(
            {"service_info.service_now_id": svc["service_info"]["service_now_id"]},
            {"$set": svc},
            upsert=True
        )

    # Sample gateways
    print("Inserting sample gateways...")
    sample_gateways = [
        {
            "_id": "dbgec2",
            "location": {"country": "Italy", "city": "Milan", "datacenter": "DC1"},
            "info": {"ip_address": "10.102.100.5", "hostname": "dbgec2.nexi.local"},
            "accessible_hosts": ["10.102.161.0/24", "10.102.170.0/24"]
        }
    ]

    for gw in sample_gateways:
        db.gateways.update_one(
            {"_id": gw["_id"]},
            {"$set": gw},
            upsert=True
        )

    print("Sample data inserted successfully!")
    print(f"  - Databases: {db.inventory_databases.count_documents({})}")
    print(f"  - Services: {db.business_services.count_documents({})}")
    print(f"  - Gateways: {db.gateways.count_documents({})}")


if __name__ == "__main__":
    seed_sample_data()
