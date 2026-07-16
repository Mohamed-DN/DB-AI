#!/usr/bin/env python3
"""
Register VirtualBox Oracle RAC databases in MongoDB CMDB.
Part of the 3-layer architecture - Execution layer.
"""
import subprocess
import json
import sys
from datetime import datetime, timezone

# MongoDB configuration
MONGO_CONTAINER = "m-dn-cmdb-mongo"
MONGO_USER = "admin"
MONGO_PASS = "admin123"
MONGO_DB = "m-dn_cmdb"
MONGO_COLLECTION = "inventory_databases"

# VirtualBox Oracle RAC configuration
VBOX_ORACLE_DATABASES = [
    {
        "identity": {
            "db_unique_name": "CDBRAC_RAC1",
            "db_name": "CDBRAC",
            "engine": "ORACLE",
            "topology": "RAC",
            "environment": "VIRTUALBOX_LAB",
            "host": "192.168.56.101",
            "datacenter": "VirtualBox",
            "gateway_ref": "REMOTE_VBOX"
        },
        "connection": {
            "type": "REMOTE",
            "host": "192.168.56.101",
            "port": 1521,
            "service_name": "cdbrac",
            "user": "c##aiauto",
            "password": "root",
            "container": "m-dn-oracle-cairo-primary" # Jump host
        },
        "configuration": {
            "version": "19.3.0.0",
            "port": 1521,
            "oracle_specific": {
                "architecture": "CDB",
                "cluster_name": "rac-cluster",
                "pdbs": [
                    { "name": "PDB1", "status": "READ WRITE", "open_mode": "READ WRITE" },
                    { "name": "SOLE", "status": "READ WRITE", "open_mode": "READ WRITE" },
                    { "name": "LUNA", "status": "READ WRITE", "open_mode": "READ WRITE" }
                ]
            }
        },
        "state": {
            "status": "UP",
            "last_seen": None
        },
        # Adding missing sections from schema
        "nodes": [
            {
                "node_name": "rac1",
                "hostname": "rac1.localdomain",
                "host_ip": "192.168.56.101",
                "role": "PRIMARY",
                "status": "OPEN",
                 "host_specs": {
                    "os": { "distro": "Oracle Linux", "version": "7.9" },
                    "cpu": { "model": "VBox CPU", "cores_per_socket": 2 }
                }
            }
        ],
        "licensing": { "product_edition": "ENTERPRISE", "active_options": ["RAC"] },
        "storage": { "asm_diskgroups": [{ "name": "DATA", "state": "MOUNTED", "used_pct": 45 }] }
    },
    {
        "identity": {
            "db_unique_name": "CDBRAC_RAC2",
            "db_name": "CDBRAC",
            "engine": "ORACLE",
            "topology": "RAC",
            "environment": "VIRTUALBOX_LAB",
            "host": "192.168.56.102",
            "datacenter": "VirtualBox",
            "gateway_ref": "REMOTE_VBOX"
        },
        "connection": {
            "type": "REMOTE",
            "host": "192.168.56.102",
            "port": 1521,
            "service_name": "cdbrac",
            "user": "c##aiauto",
            "password": "root",
            "container": "m-dn-oracle-cairo-primary"
        },
         "configuration": {
            "version": "19.3.0.0",
            "port": 1521,
            "oracle_specific": {
                "architecture": "CDB",
                "cluster_name": "rac-cluster",
                "pdbs": [
                   { "name": "PDB1", "status": "READ WRITE", "open_mode": "READ WRITE" },
                   { "name": "SOLE", "status": "READ WRITE", "open_mode": "READ WRITE" },
                   { "name": "LUNA", "status": "MOUNTED", "open_mode": "MOUNTED" }
                ]
            }
        },
        "state": {
            "status": "UP",
            "last_seen": None
        },
        "nodes": [
            {
                "node_name": "rac2",
                "hostname": "rac2.localdomain",
                "host_ip": "192.168.56.102",
                "role": "SECONDARY",
                "status": "OPEN"
            }
        ]
    }
]

def execute_mongo_command(js_command):
    """Execute a mongosh command and return result"""
    cmd = [
        "docker", "exec", MONGO_CONTAINER,
        "mongosh", MONGO_DB,
        "--username", MONGO_USER,
        "--password", MONGO_PASS,
        "--authenticationDatabase", "admin",
        "--quiet",
        "--eval", js_command
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return None
    return result.stdout.strip()

def register_database(db_data):
    """Register or update a database in MongoDB"""
    db_data["state"]["last_seen"] = datetime.now(timezone.utc).isoformat()
    
    db_name = db_data["identity"]["db_unique_name"]
    
    js_cmd = f"""
    db.{MONGO_COLLECTION}.updateOne(
        {{ "identity.db_unique_name": "{db_name}" }},
        {{ $set: {json.dumps(db_data)} }},
        {{ upsert: true }}
    )
    """
    
    result = execute_mongo_command(js_cmd)
    if result:
        print(f"[OK] Registered: {db_name}")
        return True
    else:
        print(f"[FAIL] Failed: {db_name}", file=sys.stderr)
        return False

def main():
    print("Registering VirtualBox Oracle RAC databases...")
    success = 0
    for db in VBOX_ORACLE_DATABASES:
        if register_database(db):
            success += 1
    
    print(f"\nRegistered {success}/{len(VBOX_ORACLE_DATABASES)} VirtualBox Oracle databases")
    return 0 if success == len(VBOX_ORACLE_DATABASES) else 1

if __name__ == "__main__":
    sys.exit(main())
