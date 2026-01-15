"""
Migration Script: Move Storage Data to Dedicated Collection
This script extracts storage data from inventory_databases and creates
documents in the new inventory_storage collection, then updates the
original documents to have only a storage_summary.
"""
from pymongo import MongoClient
import datetime
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env.v2')

# Connect to MongoDB
mongo_uri = f"mongodb://{os.getenv('MONGO_USERNAME')}:{os.getenv('MONGO_PASSWORD')}@localhost:{os.getenv('MONGODB_PORT', '28017')}/?authSource=admin"
client = MongoClient(mongo_uri)
db = client[os.getenv('MONGODB_DB', 'nexi_cmdb_v2')]

inventory_dbs = db['inventory_databases']
inventory_storage = db['inventory_storage']

# Create index on db_ref for efficient lookups
inventory_storage.create_index("db_ref", unique=True)

print("🔄 Migrating storage data to inventory_storage collection...")

migrated_count = 0
for doc in inventory_dbs.find({"storage": {"$exists": True}}):
    db_name = doc.get('identity', {}).get('db_unique_name')
    engine = doc.get('identity', {}).get('engine', 'UNKNOWN')
    storage_data = doc.get('storage', {})
    
    if not db_name:
        continue
    
    # Build storage document
    storage_doc = {
        "db_ref": db_name,
        "engine": engine,
        "items": [],
        "last_updated": datetime.datetime.now()
    }
    
    # Oracle: disk_groups + tablespaces
    if 'disk_groups' in storage_data:
        for dg in storage_data['disk_groups']:
            total = dg.get('total_mb', 0)
            free = dg.get('free_mb', 0)
            used_pct = round((1 - free / total) * 100, 1) if total > 0 else 0
            storage_doc['items'].append({
                "type": "ASM_DISKGROUP",
                "name": dg.get('name'),
                "state": dg.get('state'),
                "redundancy": dg.get('type'),
                "total_mb": total,
                "free_mb": free,
                "used_pct": used_pct
            })
    
    if 'tablespaces' in storage_data:
        for ts in storage_data['tablespaces']:
            storage_doc['items'].append({
                "type": "TABLESPACE",
                "name": ts.get('name'),
                "used_pct": ts.get('used_pct'),
                "used_gb": ts.get('used_gb'),
                "max_gb": ts.get('max_gb')
            })
    
    # PostgreSQL: WAL, PGDATA
    if 'wal' in storage_data:
        wal = storage_data['wal']
        storage_doc['items'].append({
            "type": "WAL_ARCHIVE",
            "archive_mode": wal.get('archive_mode'),
            "archive_command": wal.get('archive_command'),
            "wal_level": wal.get('wal_level'),
            "pending_files": wal.get('pending_files', 0)
        })
    
    if 'pgdata' in storage_data:
        pgdata = storage_data['pgdata']
        storage_doc['items'].append({
            "type": "PGDATA",
            "data_dir": pgdata.get('data_dir'),
            "used_mb": pgdata.get('used_mb'),
            "available_mb": pgdata.get('available_mb')
        })
    
    # Upsert into inventory_storage
    if storage_doc['items']:
        inventory_storage.update_one(
            {"db_ref": db_name},
            {"$set": storage_doc},
            upsert=True
        )
        migrated_count += 1
        
        # Calculate summary for the original document
        total_size = storage_data.get('total_size', 'Unknown')
        total_bytes = storage_data.get('total_size_bytes', 0)
        
        # Rough free calculation from disk groups
        total_disk_mb = sum(dg.get('total_mb', 0) for dg in storage_data.get('disk_groups', []))
        free_disk_mb = sum(dg.get('free_mb', 0) for dg in storage_data.get('disk_groups', []))
        free_pct = round((free_disk_mb / total_disk_mb) * 100, 1) if total_disk_mb > 0 else 0
        
        # Update original document: replace storage with storage_summary
        inventory_dbs.update_one(
            {"_id": doc['_id']},
            {
                "$set": {
                    "storage_summary": {
                        "total_size": total_size,
                        "total_size_bytes": total_bytes,
                        "free_pct": free_pct,
                        "storage_ref": db_name
                    }
                },
                "$unset": {"storage": ""}
            }
        )
        print(f"  ✅ Migrated: {db_name} ({len(storage_doc['items'])} items)")

print(f"\n🎉 Migration complete! {migrated_count} databases processed.")
print(f"   New collection: inventory_storage ({inventory_storage.count_documents({})}) docs")
