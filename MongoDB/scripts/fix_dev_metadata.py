
import sys
import os
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Orchestrator'))
from src.mongo_proxy import MongoProxy

def fix_dev_metadata():
    mongo = MongoProxy()
    
    # 1. Milano DEV
    mongo.execute_eval("""
    db.inventory_databases.updateOne(
        { "identity.container_name": "nexi-pg-milano-dev" },
        { 
            $set: {
                "identity.name": "PG Milano DEV",
                "identity.type": "DEV",
                "identity.db_engine": "POSTGRES",
                "identity.host": "pg-milano-dev.nexi.lab",
                "identity.port": 5433,
                "configuration": {
                    "version": "15",
                    "port": 5433,
                    "max_connections": 100
                },
                "location": {
                    "datacenter": "Milano DC1",
                    "rack": "R02",
                    "server": "SRV-DEV-01"
                }
            }
        },
        { upsert: true }
    )
    """)
    print("Fixed nexi-pg-milano-dev")

    # 2. Bratislava DEV
    mongo.execute_eval("""
    db.inventory_databases.updateOne(
        { "identity.container_name": "nexi-pg-bratislava-dev" },
        { 
            $set: {
                "identity.name": "PG Bratislava DEV",
                "identity.type": "DEV",
                "identity.db_engine": "POSTGRES",
                "identity.host": "pg-bratislava-dev.nexi.lab",
                "identity.port": 5434,
                "configuration": {
                    "version": "15",
                    "port": 5434,
                    "max_connections": 100
                },
                "location": {
                    "datacenter": "Bratislava DC2",
                    "rack": "R01",
                    "server": "SRV-DEV-02"
                }
            }
        },
        { upsert: true }
    )
    """)
    print("Fixed nexi-pg-bratislava-dev")

if __name__ == "__main__":
    fix_dev_metadata()
