"""Reset admin password in MongoDB"""
import os
import sys
import pymongo
import bcrypt

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:nexi2024@localhost:28017/?authSource=admin")
DB_NAME = "nexi_cmdb_v2"
NEW_PASSWORD = "nexi2024"

def main():
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[DB_NAME]
        
        # Generate bcrypt hash
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(NEW_PASSWORD.encode('utf-8'), salt).decode('utf-8')
        
        print(f"New hash: {password_hash}")
        
        # Update admin password
        result = db.users.update_one(
            {"username": "admin"},
            {"$set": {"password_hash": password_hash}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Password reset successful for 'admin'")
            print(f"   New password: {NEW_PASSWORD}")
        else:
            print("⚠️ No changes made (user might not exist)")
            # Try to create admin if not exists
            existing = db.users.find_one({"username": "admin"})
            if not existing:
                print("Creating admin user...")
                from datetime import datetime
                db.users.insert_one({
                    "username": "admin",
                    "email": "admin@nexi.lab",
                    "full_name": "System Administrator",
                    "role": "admin",
                    "databases_scope": ["*"],
                    "is_active": True,
                    "password_hash": password_hash,
                    "created_at": datetime.utcnow()
                })
                print(f"✅ Created admin user with password: {NEW_PASSWORD}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
