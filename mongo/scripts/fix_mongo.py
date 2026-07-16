import sys
import os
import datetime
sys.path.append(os.getcwd())
from Orchestrator.src.mongo_proxy import MongoProxy

try:
    m = MongoProxy()
    
    # Document for m-dn-cmdb-mongo
    doc = {
        "identity": {
            "db_unique_name": "M-DN_CMDB_MONGO",
            "db_name": "m-dn-cmdb-mongo", # Container name
            "engine": "MONGODB",
            "topology": "STANDALONE",
            "environment": "DOCKER_LAB"
        },
        "connection": {
            "type": "DOCKER",
            "container": "m-dn-cmdb-mongo",
            "host": "localhost",
            "port": 28017
        },
        "state": {
            "status": "UP",
            "last_seen": datetime.datetime.utcnow().isoformat()
        },
        "configuration": {
            "version": "7.0",
            "url": "mongodb://admin:admin123@localhost:28017"
        }
    }
    
    # Upsert
    m.upsert_database(doc)
    print("✅ Added/Updated M-DN_CMDB_MONGO")
    
    # Clean others if they exist now
    m.execute_eval("db.inventory_databases.deleteMany({'identity.db_unique_name': {$in: ['mongodb', 'm-dn-mongodb']}})")
    print("✅ Cleaned duplicates")

except Exception as e:
    print(f"Error: {e}")
