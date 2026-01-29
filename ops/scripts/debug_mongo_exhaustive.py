
from pymongo import MongoClient
import json

def diag():
    # Test both localhost and 127.0.0.1
    targets = ["localhost", "127.0.0.1"]
    port = 28017
    
    for host in targets:
        print(f"\n--- Testing Host: {host} ---")
        uri = f"mongodb://admin:nexi2024@{host}:{port}/?authSource=admin"
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            dbs = client.list_database_names()
            print(f"Databases: {dbs}")
            
            for db_name in ["nexi_cmdb_v2", "nexi_cmdb"]:
                if db_name in dbs:
                    print(f"  📂 DB: {db_name}")
                    db = client[db_name]
                    cols = db.list_collection_names()
                    print(f"    Collections: {cols}")
                    if "oem_instances" in cols:
                        count = db.oem_instances.count_documents({})
                        print(f"    ⭐ oem_instances count: {count}")
        except Exception as e:
            print(f"    ❌ Error: {e}")

if __name__ == "__main__":
    diag()
