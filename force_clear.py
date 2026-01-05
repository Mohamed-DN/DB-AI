import sys
import os
sys.path.append(os.getcwd())
try:
    from Orchestrator.src.mongo_proxy import MongoProxy
    mongo = MongoProxy()
    print("Force clearing alerts...")
    # Update all processed=false to processed=true
    res = mongo.execute_eval("db.monitoring_alerts.updateMany({processed: false}, {$set: {processed: true}})")
    print(f"Result: {res}")
    print("✅ Alerts Cleared. GPU should drop momentarily.")
except Exception as e:
    print(f"Error: {e}")
