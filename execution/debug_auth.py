
import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from api_agents.api_gateway import config
from api_agents.api_gateway.services.auth_service import get_auth_service

async def test_auth():
    print("🚀 Testing Auth Service...")
    try:
        auth = get_auth_service()
        print(f"   Mongo URI: {auth.mongo_uri}")
        
        print("   Connecting to DB...")
        db = await auth._get_db()
        print("   Connection object obtained.")
        
        print("   Finding admin user...")
        user = await auth.get_user("admin")
        
        if user:
            print(f"   ✅ Admin found: {user.username}")
            print(f"   Auth verify: {auth.verify_password('NexiAdmin2024!', user.password_hash)}")
        else:
            print("   ❌ Admin user NOT found!")
            
    except Exception as e:
        print(f"   🔥 EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_auth())
