
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api_agents.api_gateway.services.auth_service import get_auth_service
from api_agents.api_gateway.models.user import UserCreate, UserRole
import asyncio

def create_admin():
    print("Initializing Auth Service...")
    auth = get_auth_service()
    
    print("Creating Admin User...")
    try:
        # Note: create_user is async in the service definition (I made it async def but implemented it sync? No, I made it async def and removed await in router, but service implementation is sync logic?)
        # Let's check my rewrite of auth_service.py. 
        # I defined methods as `async def`?
        # Step 1928: `async def create_user`. But inside it does `db = next(self.pg_service.get_db())`.
        # So it is a coroutine. I must await it.
        
        user = asyncio.run(auth.create_user(UserCreate(
            username="admin",
            email="admin@nexi.lab",
            full_name="System Administrator",
            role=UserRole.ADMIN,
            password="NexiAdmin2024!",
            is_active=True
        )))
        print(f"✅ User created: {user.username} with role {user.role}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_admin()
