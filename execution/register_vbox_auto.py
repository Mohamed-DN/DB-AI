import sys
import os
import json

# Add path to Orchestrator src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Orchestrator/src')))
try:
    from mongo_proxy import MongoProxy
except ImportError:
    # Try alternate path if running from subdir
    sys.path.append(os.path.abspath('../Orchestrator/src'))
    from mongo_proxy import MongoProxy

def register_dbs():
    mongo = MongoProxy()
    
    dbs = [
        {
            "name": "M-DN-ORACLE-RAC1",
            "host": "192.168.56.101",
            "service": "cdbrac", 
            "user": "sys",
            "password": "root"
        },
        {
            "name": "M-DN-ORACLE-RAC2",
            "host": "192.168.56.102",
            "service": "cdbrac",
            "user": "sys",
            "password": "root"
        }
    ]
    
    print("=== Registering Databases ===")
    for db in dbs:
        doc = {
            "identity": {
                "db_unique_name": db["name"],
                "db_name": db["service"],
                "engine": "ORACLE",
                "environment": "DEV", 
                "topology": "RAC_NODE"
            },
            "connection": {
                "type": "REMOTE",
                "host": db["host"],
                "port": 1521,
                "service_name": db["service"],
                "user": db["user"],
                "password": db["password"]
            },
            "state": {
                "status": "UNKNOWN",
                "metrics": {}
            }
        }
        
        doc_json = json.dumps(doc)
        mongo.execute_eval(f"db.inventory_databases.updateOne({{'identity.db_unique_name': '{db['name']}'}}, {{$set: {doc_json}}}, {{upsert: true}})")
        print(f"[OK] Registered {db['name']} ({db['host']})")

if __name__ == "__main__":
    register_dbs()
