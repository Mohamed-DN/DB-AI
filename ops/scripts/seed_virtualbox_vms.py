"""
Seed VirtualBox Oracle VMs in MongoDB
=====================================
Aggiunge le VM VirtualBox Oracle alla collection inventory_databases
per l'auto-discovery del monitoring.
"""
from pymongo import MongoClient
from datetime import datetime

MONGO_URI = "mongodb://admin:nexi2024@localhost:28017/"
MONGO_DB = "nexi_cmdb_v2"

VMS = [
    {
        "_id": "ORACLE_VM1_DEV",
        "identity": {
            "db_unique_name": "ORACLE_VM1_DEV",
            "host": "127.0.0.1",
            "port": 2521,
            "sid": "ORCL",
            "service_name": "",
            "type": "ORACLE",
            "engine": "ORACLE"
        },
        "connection_info": {
            "monitoring_user": "system",
            "monitoring_password": "root"
        },
        "datacenter": "VIRTUALBOX_DEV",
        "environment": "development",
        "status": "active",
        "description": "VirtualBox Oracle VM 1 - Development",
        "last_seen": datetime.utcnow(),
        "source": "manual_seed"
    },
    {
        "_id": "ORACLE_VM2_DEV",
        "identity": {
            "db_unique_name": "ORACLE_VM2_DEV",
            "host": "127.0.0.1",
            "port": 2522,
            "sid": "ORCL",
            "service_name": "",
            "type": "ORACLE",
            "engine": "ORACLE"
        },
        "connection_info": {
            "monitoring_user": "system",
            "monitoring_password": "root"
        },
        "datacenter": "VIRTUALBOX_DEV",
        "environment": "development",
        "status": "active",
        "description": "VirtualBox Oracle VM 2 - Development",
        "last_seen": datetime.utcnow(),
        "source": "manual_seed"
    }
]

def main():
    print("📦 Seeding VirtualBox Oracle VMs to MongoDB...")
    
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    
    for vm in VMS:
        result = db.inventory_databases.update_one(
            {"_id": vm["_id"]},
            {"$set": vm},
            upsert=True
        )
        
        if result.upserted_id:
            print(f"  ✅ Inserted: {vm['_id']}")
        else:
            print(f"  🔄 Updated: {vm['_id']}")
    
    print(f"\n✅ Done! {len(VMS)} VMs added to inventory_databases")
    print("\n📊 Now you can run:")
    print("   python ops/scripts/oem_scraper.py --discover-from-mongo --once")
    
    client.close()

if __name__ == "__main__":
    main()
