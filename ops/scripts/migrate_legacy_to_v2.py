import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Config
URI = "mongodb://localhost:27017/"
LEGACY_DB = "fabridb"
TARGET_DB = "nexi_cmdb_v2"

async def migrate():
    client = AsyncIOMotorClient(URI)
    legacy = client[LEGACY_DB]
    target = client[TARGET_DB]
    
    print(f"🚀 Starting Migration: {LEGACY_DB}.cmdb -> {TARGET_DB}.inventory_databases")
    
    # 1. Fetch Legacy Data
    cursor = legacy.cmdb.find({})
    total = await legacy.cmdb.count_documents({})
    print(f"Found {total} legacy documents.")
    
    batch = []
    processed = 0
    
    async for doc in cursor:
        # Transformation Logic
        new_doc = {
            "identity": {
                "db_unique_name": doc.get("DB_UNIQUE_NAME", doc.get("SID", "UNKNOWN")),
                "engine": "ORACLE", # Assuming mostly Oracle based on legacy fields
                "topology": doc.get("CLUSTER", "SINGLE"),
                "is_rac": doc.get("CLUSTER") == "RAC"
            },
            "state": {
                "status": doc.get("STATUS", "UNKNOWN"),
                "uptime": doc.get("UPTIME"),
                "last_check": datetime.utcnow()
            },
            "configuration": {
                "version": doc.get("VERSION"),
                "oracle_home": doc.get("ORACLE_HOME"),
                "environment": doc.get("ENV", "PRODUCTION")
            },
            "connection": {
                "host": doc.get("HOST_NAME"),
                "port": doc.get("PORT", "1521"),
                "service_name": doc.get("SERVICE_NAME")
            },
            "metadata": {
                "migrated_from": "fabridb",
                "migration_date": datetime.utcnow(),
                "legacy_id": str(doc.get("_id"))
            }
        }
        
        # Determine Engine if possible
        if "POSTGRES" in str(doc).upper():
            new_doc["identity"]["engine"] = "POSTGRES"
            
        batch.append(new_doc)
        
        if len(batch) >= 1000:
            await target.inventory_databases.insert_many(batch)
            processed += len(batch)
            print(f"Migrated {processed}/{total} databases...")
            batch = []
            
    if batch:
        await target.inventory_databases.insert_many(batch)
        processed += len(batch)
        
    print(f"✅ Migration Complete. Total: {processed}")
    
    # Migrate Alerts (Error History)
    print(f"🚀 Starting Alerts Migration: {LEGACY_DB}.error_histori -> {TARGET_DB}.monitoring_alerts")
    alert_cursor = legacy.error_histori.find().limit(1000) # Limit for speed, user can background full migration later
    total_alerts = 1000
    
    alert_batch = []
    async for alert in alert_cursor:
        new_alert = {
            "severity": "CRITICAL" if "ORA-" in str(alert.get("ERROR_TEXT", "")) else "WARNING",
            "message": alert.get("ERROR_TEXT", "Unknown Error"),
            "timestamp": alert.get("TIMESTAMP", datetime.utcnow()),
            "source": alert.get("DB_NAME", "UNKNOWN"),
            "processed": False,
            "type": "LEGACY_ERROR",
            "db_name": alert.get("DB_NAME")
        }
        alert_batch.append(new_alert)
        
    if alert_batch:
        await target.monitoring_alerts.insert_many(alert_batch)
        print(f"Migrated {len(alert_batch)} recent alerts.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(migrate())
