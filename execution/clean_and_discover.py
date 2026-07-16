"""
Clean Inventory and Run Discovery
================================
1. Wipes inventory_databases collection
2. Ensures gateway-cairo exists
3. Runs Discovery Agent
4. Reports findings
"""
import sys
import os
import time
from pymongo import MongoClient
from datetime import datetime

# Setup paths
sys.path.append(os.getcwd())

# Ensure Env Vars for V2
os.environ["MONGODB_DB"] = "m-dn_cmdb_v2"
os.environ["MONGO_CONTAINER"] = "m-dn-mongodb"
os.environ["MONGO_USERNAME"] = "admin"
os.environ["MONGO_PASSWORD"] = "admin123"

from api_agents.workers.discovery.discovery_agent import DiscoveryAgent

def clean_and_discover():
    # 1. Connect and Clean
    c = MongoClient('localhost', 28017, username='admin', password='pippopippo_1234')
    db = c['m-dn_cmdb_v2']
    
    deleted = db.inventory_databases.delete_many({})
    print(f"🧹 CLEANUP: Removed {deleted.deleted_count} databases from inventory.")
    
    # 2. Verify Gateway
    gateway = db.gateways.find_one({'_id': 'gateway-cairo'})
    if not gateway:
        print("⚠️ Gateway Cairo missing! Creating...")
        db.gateways.insert_one({
            '_id': 'gateway-cairo',
            'name': 'Cairo Lab Gateway',
            'target_hosts': [
                {'ip_address': '192.168.56.101', 'ssh_user': 'oracle', 'ssh_password': 'root', 'db_port': 1521, 'db_user': 'sys', 'db_password': 'root'},
                {'ip_address': '192.168.56.102', 'ssh_user': 'oracle', 'ssh_password': 'root', 'db_port': 1521, 'db_user': 'sys', 'db_password': 'root'}
            ],
            'status': 'ACTIVE',
            'created_at': datetime.now().isoformat()
        })
    else:
        print("✅ Gateway Cairo confirmed.")
        
    # 3. Run Discovery
    print("\n🕵️ STARTING DISCOVERY...")
    agent = DiscoveryAgent()
    agent.run_once()
    
    # 4. Report
    print("\n📊 FINAL REPORT:")
    all_dbs = list(db.inventory_databases.find({}))
    print(f"Total Databases: {len(all_dbs)}")
    
    print("\n--- ORACLE (Target) ---")
    oracles = [d for d in all_dbs if d.get('identity', {}).get('family') == 'ORACLE']
    for o in oracles:
        ident = o.get('identity', {})
        print(f"✅ {ident.get('db_unique_name')} ({ident.get('role')}) on {ident.get('host')}")
        
    print("\n--- OTHERS (Docker/Local) ---")
    others = [d for d in all_dbs if d not in oracles]
    for o in others:
        ident = o.get('identity', {})
        print(f"🔹 {ident.get('db_unique_name')} ({ident.get('engine')})")

if __name__ == "__main__":
    clean_and_discover()
