
import os
import sys
import argparse
from pymongo import MongoClient
from datetime import datetime, timedelta

# Add root path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Connection details
MONGO_HOST = os.getenv("MONGODB_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGODB_PORT", "27017"))
MONGO_USER = os.getenv("MONGO_USERNAME", "admin")
MONGO_PASS = os.getenv("MONGO_PASSWORD", "nexi2024")
MONGO_DB = os.getenv("MONGODB_DB", "nexi_cmdb_v2")

def check_deep_state():
    print(f"🕵️ Starting Deep System Inspection...")
    print(f"   Time: {datetime.utcnow().isoformat()} UTC")
    
    uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        db = client[MONGO_DB]
        client.admin.command('ping')
        print("✅ MongoDB Connection: OK")
    except Exception as e:
        print(f"❌ MongoDB Connection FAILED: {e}")
        return False

    all_good = True

    # 1. Check Enricher Activity
    print("\n📊 Checking Enricher Activity (inventory_databases)...")
    try:
        recent_enrichment = db.inventory_databases.count_documents({
            "metadata.last_enriched": {"$gte": (datetime.utcnow() - timedelta(minutes=15)).isoformat()}
        })
        total_dbs = db.inventory_databases.count_documents({})
        print(f"   Found {total_dbs} databases total.")
        print(f"   Databases enriched in last 15 min: {recent_enrichment}")
        
        if recent_enrichment > 0:
            print("   ✅ Enricher is ACTIVE.")
        else:
            print("   ⚠️ Enricher seems silent (or no DBs to enrich).")
            # Not necessarily a failure if no DBs are reachable, but worth noting
    except Exception as e:
        print(f"   ❌ Error checking Enricher: {e}")
        all_good = False

    # 2. Check Sentinel Activity
    print("\n🛡️ Checking Sentinel Activity (monitoring_alerts)...")
    try:
        recent_alerts = db.monitoring_alerts.count_documents({
            "timestamp": {"$gte": datetime.utcnow() - timedelta(minutes=30)}
        })
        print(f"   Alerts generated in last 30 min: {recent_alerts}")
        
        # Check for Sentinel specific alerts
        sentinel_alerts = db.monitoring_alerts.count_documents({
            "source": "SentinelWorkflow"
        })
        print(f"   Total Sentinel Alerts (All Time): {sentinel_alerts}")
        
        if sentinel_alerts > 0:
             print("   ✅ Sentinel has historically generated alerts.")
        else:
             print("   ℹ️ No Sentinel alerts yet (System might be healthy or just started).")
             
    except Exception as e:
        print(f"   ❌ Error checking Sentinel: {e}")
        all_good = False

    # 3. Check System Scripts (Migration Verification)
    print("\n📜 Checking API/Script Repository (system_scripts)...")
    try:
        script_count = db.system_scripts.count_documents({})
        print(f"   Scripts stored in DB: {script_count}")
        if script_count > 5:
            print("   ✅ Script migration confirmed.")
        else:
            print("   ❌ Script repository looks empty.")
            all_good = False
    except Exception as e:
         print(f"   ❌ Error checking scripts: {e}")
         all_good = False

    return all_good

if __name__ == "__main__":
    success = check_deep_state()
    if success:
        print("\n✅ Deep Inspection PASSED. System is vital.")
        sys.exit(0)
    else:
        print("\n⚠️ Deep Inspection found issues.")
        sys.exit(1)
