import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "nexi_cmdb_v2"

async def check_and_fix():
    print(f"Connecting to {MONGO_URI}...")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    
    # Check Inventory
    count = await db.inventory_databases.count_documents({})
    print(f"Current Inventory Count: {count}")
    
    if count == 0:
        print("Inventory is empty. Populating sample data...")
        sample_dbs = [
            {
                "identity": {"db_unique_name": "CRM_PROD", "engine": "ORACLE", "topology": "RAC"},
                "state": {"status": "UP", "uptime": "45d"},
                "configuration": {"version": "19.21"},
                "connection": {"host": "10.0.0.5", "port": 1521}
            },
            {
                "identity": {"db_unique_name": "BILLING_DB", "engine": "POSTGRES", "topology": "SINGLE"},
                "state": {"status": "UP", "uptime": "12d"},
                "configuration": {"version": "15.3"},
                "connection": {"host": "10.0.0.8", "port": 5432}
            },
            {
                "identity": {"db_unique_name": "LEGACY_HR", "engine": "ORACLE", "topology": "SINGLE"},
                "state": {"status": "DOWN", "uptime": "0"},
                "configuration": {"version": "11.2"},
                "connection": {"host": "10.0.0.9", "port": 1521}
            }
        ]
        await db.inventory_databases.insert_many(sample_dbs)
        print("Inserted 3 sample databases.")
    else:
        print("Inventory has data.")
        cursor = db.inventory_databases.find().limit(3)
        async for doc in cursor:
            print(f"- {doc.get('identity', {}).get('db_unique_name')} ({doc.get('state', {}).get('status')})")

    # Check Alerts
    alert_count = await db.monitoring_alerts.count_documents({})
    print(f"Current Alert Count: {alert_count}")
    if alert_count == 0:
         print("Alerts empty. Populating sample alert...")
         await db.monitoring_alerts.insert_one({
             "severity": "CRITICAL",
             "message": "Tablespace USERS is 98% full",
             "timestamp": datetime.utcnow(),
             "source": "CRM_PROD",
             "processed": False,
             "type": "SENTINEL_CRITICAL",
             "db_name": "CRM_PROD"
         })
         print("Inserted sample alert.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_and_fix())
