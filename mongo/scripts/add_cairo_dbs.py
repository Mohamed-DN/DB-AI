import sys
import os
import datetime

# Add project root to path
sys.path.append(os.path.abspath("c:/AI-M-DN/M-DN_DB_AI"))

from Orchestrator.src.mongo_proxy import MongoProxy

def add_cairo_dbs():
    mongo = MongoProxy()
    
    # Define Databases
    dbs = [
        {
            "identity": {
                "db_unique_name": "M-DN-ORACLE-CAIRO-PRIMARY",
                "db_name": "m-dn-oracle-cairo-primary",
                "engine": "ORACLE",
                "environment": "PROD",
                "host": "172.20.3.10",
                "port": 1521
            },
            "state": {
                "status": "UP",
                "last_check": datetime.datetime.now().isoformat()
            },
            "replication": {
                "enabled": True,
                "type": "GOLDENGATE",
                "role": "PRIMARY",
                "partner_instance": "M-DN-ORACLE-CAIRO-REPLICA",
                "lag_seconds": 0
            },
            "location": {
                "datacenter": "CAIRO-DC1",
                "region": "MEA"
            }
        },
        {
            "identity": {
                "db_unique_name": "M-DN-ORACLE-CAIRO-REPLICA",
                "db_name": "m-dn-oracle-cairo-replica",
                "engine": "ORACLE",
                "environment": "DR",
                "host": "172.20.3.11",
                "port": 1521
            },
            "state": {
                "status": "UP",
                "last_check": datetime.datetime.now().isoformat()
            },
            "replication": {
                "enabled": True,
                "type": "GOLDENGATE",
                "role": "REPLICA",
                "partner_instance": "M-DN-ORACLE-CAIRO-PRIMARY",
                "lag_seconds": 2
            },
            "location": {
                "datacenter": "CAIRO-DC2",
                "region": "MEA"
            }
        }
    ]
    
    # Insert
    for db in dbs:
        # Check if exists
        exists = mongo.execute_eval(f"db.inventory_databases.findOne({{'identity.db_unique_name': '{db['identity']['db_unique_name']}'}})")
        if not exists:
            # We need to use insertOne but via proxy we might need to rely on python dict passing
            # Since execute_eval returns JSON, passing complex objects via string eval is risky.
            # However, MongoProxy likely has methods or we can use the eval with simple JSON
            # For simplicity in this env, we might need a direct insert helper or valid JSON string.
            import json
            json_str = json.dumps(db)
            mongo.execute_eval(f"db.inventory_databases.insertOne({json_str})")
            print(f"Added {db['identity']['db_unique_name']}")
        else:
            print(f"Skipping {db['identity']['db_unique_name']} (already exists)")

if __name__ == "__main__":
    add_cairo_dbs()
