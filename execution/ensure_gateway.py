
from pymongo import MongoClient
import os

def ensure_gateway():
    print("🔌 Connecting to MongoDB...")
    client = MongoClient("mongodb://admin:pippopippo_1234@localhost:28017/")
    db = client["m-dn_cmdb_v2"]
    
    gateway_cairo = {
        "_id": "m-dn-gw-cairo",
        "name": "Cairo Gateway",
        "region": "CAIRO",
        "type": "SSH",
        "host": "192.168.56.1", # Host machine IP usually reachable from VBox
        "status": "ACTIVE",
        "target_hosts": [
            {
                "ip_address": "192.168.56.101",
                "hostname": "rac1",
                "ssh_user": "root",
                "ssh_password": "root", # Typical VBox generic pass
                "db_port": 1521,
                "db_user": "sys",
                "db_password": "root"
            },
            {
                "ip_address": "192.168.56.102",
                "hostname": "rac2",
                "ssh_user": "root",
                "ssh_password": "root",
                "db_port": 1521
            }
        ],
        "created_at": "2026-01-15T00:00:00"
    }
    
    # Upsert
    db.gateways.update_one(
        {"_id": gateway_cairo["_id"]},
        {"$set": gateway_cairo},
        upsert=True
    )
    print("✅ Gateway 'm-dn-gw-cairo' upserted successfully.")
    
    # Allow time for propagation if needed (not really needed for Mongo)
    print("Gateway Config:")
    print(gateway_cairo)

if __name__ == "__main__":
    ensure_gateway()
