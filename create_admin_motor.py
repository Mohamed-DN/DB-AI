"""Create admin user directly with motor and correct bcrypt hash"""
import asyncio
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def create_admin():
    # Generate correct bcrypt hash
    password = b"admin123"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    password_hash = hashed.decode('utf-8')
    
    print(f"Generated hash: {password_hash}")
    print(f"Hash length: {len(password_hash)}")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://admin:nexi2024@localhost:28017/?authSource=admin")
    db = client["nexi_cmdb_v2"]
    
    # Delete existing admin
    result = await db.users.delete_many({"username": "admin"})
    print(f"Deleted {result.deleted_count} existing admin users")
    
    # Insert new admin
    user_doc = {
        "username": "admin",
        "email": "admin@nexi.lab",
        "full_name": "System Administrator",
        "role": "admin",
        "databases_scope": ["*"],
        "is_active": True,
        "password_hash": password_hash,
        "created_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_doc)
    print(f"Inserted admin user with ID: {result.inserted_id}")
    
    # Verify
    saved = await db.users.find_one({"username": "admin"})
    print(f"Saved hash: {saved['password_hash']}")
    print(f"Saved hash length: {len(saved['password_hash'])}")
    
    # Test verify
    is_valid = bcrypt.checkpw(b"admin123", saved['password_hash'].encode('utf-8'))
    print(f"Password verification: {'PASS' if is_valid else 'FAIL'}")
    
    client.close()
    print("Done!")

asyncio.run(create_admin())
