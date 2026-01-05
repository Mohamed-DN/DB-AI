
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Orchestrator'))
from src.mongo_proxy import MongoProxy

def correct_fix():
    mongo = MongoProxy()
    
    # 1. DELETE PHANTOM DOCUMENTS (My previous error)
    # The erroneous docs had "identity.container_name" which Scout doesn't use.
    print("Removing phantom documents...")
    mongo.execute_eval("""
    db.inventory_databases.deleteMany({ "identity.container_name": { $exists: true } })
    """)
    
    # 2. UPDATE CORRECT DOCUMENTS (Managed by Scout)
    # Target: NEXI-PG-MILANO-DEV
    print("Fixing NEXI-PG-MILANO-DEV...")
    mongo.execute_eval("""
    db.inventory_databases.updateOne(
        { "identity.db_unique_name": "NEXI-PG-MILANO-DEV" },
        { 
            $set: {
                "identity.db_engine": "POSTGRES",
                "identity.engine": "POSTGRES",
                "identity.type": "DEV",
                "identity.host": "pg-milano-dev.nexi.lab",
                "identity.port": 5433,
                "configuration.port": 5433,
                "configuration.version": "15",
                "location": {
                    "datacenter": "Milano DC1",
                    "rack": "R02",
                    "server": "SRV-DEV-01"
                }
            }
        }
    )
    """)

    # Target: NEXI-PG-BRATISLAVA-DEV
    print("Fixing NEXI-PG-BRATISLAVA-DEV...")
    mongo.execute_eval("""
    db.inventory_databases.updateOne(
        { "identity.db_unique_name": "NEXI-PG-BRATISLAVA-DEV" },
        { 
            $set: {
                "identity.db_engine": "POSTGRES",
                "identity.engine": "POSTGRES",
                "identity.type": "DEV",
                "identity.host": "pg-bratislava-dev.nexi.lab",
                "identity.port": 5434,
                "configuration.port": 5434,
                "configuration.version": "15",
                "location": {
                    "datacenter": "Bratislava DC2",
                    "rack": "R01",
                    "server": "SRV-DEV-02"
                }
            }
        }
    )
    """)
    
    print("Correction Complete.")

if __name__ == "__main__":
    correct_fix()
