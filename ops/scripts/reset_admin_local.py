
import pymongo
import bcrypt
from datetime import datetime

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "nexi_cmdb_v2"
NEW_PASSWORD = "NexiAdmin2024!"

def main():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(NEW_PASSWORD.encode('utf-8'), salt).decode('utf-8')
    
    result = db.users.update_one(
        {"username": "admin"},
        {"$set": {"password_hash": password_hash}}
    )
    
    if result.modified_count > 0:
        print(f"✅ Reset 'admin' password to {NEW_PASSWORD}")
    else:
        existing = db.users.find_one({"username": "admin"})
        if not existing:
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
            print(f"✅ Created 'admin' user with password {NEW_PASSWORD}")
        else:
            print("⚠️ User 'admin' already has this password or hash.")

if __name__ == "__main__":
    main()
