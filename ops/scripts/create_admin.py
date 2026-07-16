"""Temporary script to create admin user with correct password hash"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://admin:pippopippo_1234@localhost:28017")
    db = client["m-dn_cmdb_v2"]
    
    # Delete existing admin if any
    await db.users.delete_many({"username": "admin"})
    
    # Create password hash
    password_hash = pwd_context.hash("admin123")
    
    # Insert admin user
    await db.users.insert_one({
        "username": "admin",
        "email": "admin@m-dn.lab",
        "full_name": "System Administrator",
        "role": "admin",
        "databases_scope": ["*"],
        "is_active": True,
        "password_hash": password_hash
    })
    
    print("Admin user created successfully!")
    print("Username: admin")
    print("Password: admin123")
    
    client.close()

asyncio.run(create_admin())
