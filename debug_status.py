import sys
import os
import json
sys.path.append(os.getcwd())
from Orchestrator.src.mongo_proxy import MongoProxy

m = MongoProxy()
dbs = m.execute_eval("db.inventory_databases.find().toArray()")
for db in dbs:
    name = db.get('identity', {}).get('db_unique_name')
    status = db.get('state', {}).get('status', 'UNKNOWN')
    last_check = db.get('state', {}).get('last_check')
    metric_ts = db.get('state', {}).get('last_metric_update')
    print(f"{name}: {status} (Checked: {last_check}, Metrics: {metric_ts})")
