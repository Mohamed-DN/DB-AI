
import asyncio
import motor.motor_asyncio

async def test_mongo():
    uri = "mongodb://admin:nexi2024@127.0.0.1:28017/?authSource=admin"
    print(f"Connecting to {uri}...")
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(uri, serverSelectionTimeoutMS=2000)
        await client.admin.command('ping')
        print("✅ MongoDB PONG!")
    except Exception as e:
        print(f"❌ MongoDB Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_mongo())
