"""Test authentication flow directly"""
import asyncio
import sys
sys.path.insert(0, "c:\\AI-M-DN\\M-DN_DB_AI")
sys.stdout.reconfigure(encoding='utf-8')

from api_agents.api_gateway.services.auth_service import get_auth_service

async def test_auth():
    try:
        print("Getting auth service...")
        auth = get_auth_service()
        
        print("Authenticating admin/admin123...")
        user = await auth.authenticate_user("admin", "admin123")
        
        if user:
            print(f"SUCCESS! User: {user.username}, Role: {user.role}")
        else:
            print("FAILED: User not authenticated (wrong credentials or user not found)")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_auth())
