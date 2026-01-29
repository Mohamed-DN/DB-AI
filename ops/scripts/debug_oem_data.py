
from pymongo import MongoClient
import os
import sys

# Ensure we use the correct port and auth
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:nexi2024@localhost:28017/?authSource=admin")

try:
    client = MongoClient(MONGO_URI)
    db = client["nexi_cmdb_v2"]
    
    print(f"🔌 Connected to {db.name}")
    
    count = db.oem_instances.count_documents({})
    print(f"📊 OEM Instances Count: {count}")
    
    if count > 0:
        print("📝 Instances found:")
        for doc in db.oem_instances.find():
            print(f"   - {doc.get('name')} ({doc.get('url')})")
    else:
        print("❌ No OEM instances found in DB.")
        
except Exception as e:
    print(f"❌ Connection Error: {e}")
