
import os
import sys
import glob
from pymongo import MongoClient
from datetime import datetime

# Add root path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Connection details - Assuming standard lab config
MONGO_HOST = os.getenv("MONGODB_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGODB_PORT", "27017"))
MONGO_USER = os.getenv("MONGO_USERNAME", "admin")
MONGO_PASS = os.getenv("MONGO_PASSWORD", "nexi2024")
MONGO_DB = os.getenv("MONGODB_DB", "nexi_cmdb_v2")

def migrate_scripts(source_dir):
    print(f"🚀 Starting migration from {source_dir}...")
    
    # Connect to Mongo
    # Ensure authSource is set to admin
    uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
    print(f"🔌 Connecting to {MONGO_HOST}:{MONGO_PORT} as {MONGO_USER}...")
    client = MongoClient(uri)
    db = client[MONGO_DB]
    collection = db["system_scripts"]
    
    # Find scripts
    pattern = os.path.join(source_dir, "*.py")
    files = glob.glob(pattern)
    
    print(f"📋 Found {len(files)} scripts.")
    
    count = 0
    for file_path in files:
        file_name = os.path.basename(file_path)
        
        # Skip this migration script itself if running from same dir
        if "migrate_scripts_to_mongo" in file_name: 
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            doc = {
                "name": file_name,
                "type": "python",
                "source": "ops/scripts",
                "content": content,
                "description": f"Imported from {file_name}",
                "uploaded_at": datetime.utcnow(),
                "version": 1
            }
            
            # Upsert
            db.system_scripts.update_one(
                {"name": file_name},
                {"$set": doc},
                upsert=True
            )
            print(f"   ✅ Migrated: {file_name}")
            count += 1
        except Exception as e:
            print(f"   ❌ Failed to migrate {file_name}: {e}")
            
    print(f"✨ Migration complete. {count} scripts stored in '{MONGO_DB}.system_scripts'.")

if __name__ == "__main__":
    # Default to current ops/scripts directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    migrate_scripts(current_dir)
