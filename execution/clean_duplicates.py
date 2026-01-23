from pymongo import MongoClient
import sys

# Connect
try:
    client = MongoClient('localhost', 28017, username='admin', password='nexi2024')
    db = client.nexi_cmdb_v2
    collection = db.inventory_databases
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

# Find all documents
all_docs = list(collection.find({}))
print(f"Total documents before cleanup: {len(all_docs)}")

# Group by unique name
groups = {}
for doc in all_docs:
    # Try to unify name extraction
    name = None
    if 'identity' in doc and 'db_unique_name' in doc['identity']:
        name = doc['identity']['db_unique_name']
    elif 'cluster_identity' in doc and 'cluster_name' in doc['cluster_identity']:
         name = doc['cluster_identity']['cluster_name']
    elif 'database_core' in doc and 'identity' in doc['database_core']:
        name = doc['database_core']['identity'].get('db_unique_name')
    
    if not name:
        name = "UNKNOWN_OR_MISSING"
    
    if name not in groups:
        groups[name] = []
    groups[name].append(doc)

# Deduplicate
deleted_count = 0
for name, docs in groups.items():
    if len(docs) > 1:
        print(f"Found {len(docs)} entries for '{name}'. Keeping latest.")
        # Sort by _id (approximation for creation time if ObjectId) or last_seen
        # We'll use ObjectId as it's monotonic
        docs.sort(key=lambda x: x.get('_id'), reverse=True)
        
        keep = docs[0]
        remove = docs[1:]
        
        ids_to_remove = [d['_id'] for d in remove]
        result = collection.delete_many({'_id': {'$in': ids_to_remove}})
        print(f"  - Deleted {result.deleted_count} duplicates for {name}")
        deleted_count += result.deleted_count

print(f"\nCleanup complete. Removed {deleted_count} documents.")
print(f"Total documents after cleanup: {collection.count_documents({})}")
