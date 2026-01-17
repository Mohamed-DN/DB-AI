from pymongo import MongoClient
import os

# Connect
client = MongoClient('localhost', 28017, username='admin', password='nexi2024', authSource='admin')
db = client.nexi_cmdb_v2
collection = db.inventory_databases

print(f"Initial Count: {collection.count_documents({})}")

deleted_count = 0

# 1. Delete N/A or Missing names
res = collection.delete_many({"$or": [{"identity.db_unique_name": "N/A"}, {"identity.db_unique_name": None}]})
if res.deleted_count > 0:
    print(f"🗑️  Deleted {res.deleted_count} documents with invalid names (N/A).")
    deleted_count += res.deleted_count

# 2. Delete explicitly MISSING databases (ghosts)
# We might want to keep some if they are important but down, but for now user wants to clean "non ci sono"
res = collection.delete_many({"state.status": "MISSING"})
if res.deleted_count > 0:
    print(f"🗑️  Deleted {res.deleted_count} MISSING databases.")
    deleted_count += res.deleted_count

# 3. Handle V1 vs V2 duplicates (The "2" suffix ghost problem)
# Logic: If we have "NAME" and "NAME2", and "NAME" is UP/active (or exists), delete "NAME2".
all_dbs = list(collection.find({}, {"identity.db_unique_name": 1}))
db_names = {d['identity'].get('db_unique_name') for d in all_dbs if d.get('identity')}

for name in db_names:
    if not name: continue
    
    # Check if this is a "v2" name (ends with 2)
    if name.endswith("2") and not "RAC" in name: # Skip RAC2 as it might be legitimate node 2
        base_name = name[:-1] # Remove '2'
        base_name2 = name[:-2] # Maybe it was added differently? No, standard is suffix '2'
        
        # If base name exists in our list (e.g. NEXI-PG-MILANO-PROD exists for NEXI-PG-MILANO-PROD2)
        # Or if the base name without 2 is present
        if base_name in db_names:
            print(f"🔍 Found duplicate pair: {base_name} (Keep) vs {name} (Delete)")
            collection.delete_one({"identity.db_unique_name": name})
            print(f"   🗑️  Deleted {name}")
            deleted_count += 1
        else:
            # Even if base_name doesn't exist, if it's a seed artifact and we know we are running V1 names...
            # Check docker ps? No, can't easily.
            # But earlier we saw PROD and PROD2.
            # If we only have PROD2, we might keep it? 
            # But the user said "ridondanza".
            # Safe bet: if base_name is NOT in db_names, we might have ONLY the seeded V2 doc.
            # In that case, we should strictly check if it's UP.
            pass

print(f"Total Deleted: {deleted_count}")
print(f"Final Count: {collection.count_documents({})}")
