from pymongo import MongoClient
import sys

try:
    client = MongoClient('localhost', 28017, username='admin', password='pippopippo_1234')
    db = client.m-dn_cmdb_v2
    collection = db.inventory_databases
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

# RAC Nodes Configuration
updates = [
    {
        "name": "CDBRAC_RAC1",
        "update": {
            "$set": {
                "connection": {
                    "type": "REMOTE",
                    "host": "192.168.56.101",
                    "port": 1521,
                    "service_name": "CDBRAC"
                },
                "identity.gateway_ref": "gateway-cairo",
                "database_core.identity.gateway_ref": "gateway-cairo"
            }
        }
    },
    {
        "name": "CDBRAC_RAC2",
        "update": {
            "$set": {
                "connection": {
                    "type": "REMOTE",
                    "host": "192.168.56.102",
                    "port": 1521,
                    "service_name": "CDBRAC"
                },
                "identity.gateway_ref": "gateway-cairo",
                "database_core.identity.gateway_ref": "gateway-cairo"
            }
        }
    },
    {
        "name": "CDBRAC", # Cluster entry
        "update": {
             "$set": {
                "connection": {
                    "type": "REMOTE", # Cluster is virtual, but treated as remote for connection via SCAN/VIP usually
                    "host": "192.168.56.101", # Point to node 1 for now or SCAN if available
                    "port": 1521,
                    "service_name": "CDBRAC"
                },
                "identity.gateway_ref": "gateway-cairo",
                "database_core.identity.gateway_ref": "gateway-cairo"
            }
        }
    }
]

print("Applying fix for Oracle RAC connections...")

for item in updates:
    name = item['name']
    # Try finding by identity (normalized) or database_core (raw)
    query = {
        "$or": [
            {"identity.db_unique_name": name},
            {"database_core.identity.db_unique_name": name}
        ]
    }
    
    result = collection.update_one(query, item['update'])
    if result.matched_count > 0:
        print(f"✅ Updated {name} matched count: {result.matched_count} modified count: {result.modified_count}")
        # Verify
        doc = collection.find_one(query)
        print(f"   New Type: {doc.get('connection', {}).get('type')}")
    else:
        print(f"⚠️ {name} not found in inventory.")

print("\nFix complete.")
