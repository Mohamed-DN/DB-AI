
import sys
import os

# Ensure clean logging
sys.stdout.reconfigure(encoding='utf-8')

# Set environment for valid connections
os.environ["MONGODB_DB"] = "nexi_cmdb_v2"
os.environ["MONGO_CONTAINER"] = "nexi-mongodb"
os.environ["MONGO_USERNAME"] = "admin"
os.environ["MONGO_PASSWORD"] = "nexi2024" # PyMongo uses this

from api_agents.workers.Discovery.discovery_agent import DiscoveryAgent

def force_discovery():
    print("🚀 Forcing Oracle RAC Discovery...")
    agent = DiscoveryAgent()
    
    # 1. Define Target Host (simulating Gateway response)
    target_hosts = [
        {"ip_address": "192.168.56.101", "hostname": "rac1", "ssh_user": "root", "db_port": 1521},
        {"ip_address": "192.168.56.102", "hostname": "rac2", "ssh_user": "root", "db_port": 1521}
    ]
    
    gateway_id = "nexi-gw-cairo"
    
    for host in target_hosts:
        print(f"\n🔍 Scanning {host['ip_address']}...")
        # Direct Oracle Discovery
        # We pass empty existing_names to ensure it returns results
        dbs = agent.discover_oracle_direct(host, gateway_id, set())
        
        if dbs:
            print(f"   ✅ Found {len(dbs)} databases on {host['ip_address']}")
            for db_info in dbs:
                # Add host info if missing
                db_info["host"] = host['ip_address']
                
                # Transform to Inventory Document
                doc = agent.create_inventory_document(db_info)
                
                success = agent.insert_new_database(doc)
                if success:
                    print(f"      💾 Inserted: {doc.get('identity', {}).get('db_unique_name')}")
                else:
                    print(f"      ❌ Insert failed for: {doc.get('identity', {}).get('db_unique_name')}")
        else:
            print(f"   ⚠️ No databases found on {host['ip_address']}")

if __name__ == "__main__":
    force_discovery()
