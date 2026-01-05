import sys
import os
sys.path.append(os.getcwd())
from Orchestrator.src.mongo_proxy import MongoProxy
import json

mongo = MongoProxy()

print("--- System Config ---")
try:
    scout = mongo.execute_eval("db.system_config.findOne({key: 'scout_interval'})")
    print(f"Scout Interval Doc: {scout}")
    
    check = mongo.execute_eval("db.system_config.findOne({key: 'check_interval'})")
    print(f"Check Interval Doc: {check}")
except Exception as e:
    print(f"Error: {e}")

print("\n--- Database Data ---")
try:
    # Check one DB to see if db_name is correct
    db = mongo.execute_eval("db.inventory_databases.findOne({})")
    print(f"Sample DB: {db}")
    if db:
        ident = db.get('identity', {})
        print(f"db_name: {ident.get('db_name')}, host: {ident.get('host')}")
except Exception as e:
    print(f"Error: {e}")
