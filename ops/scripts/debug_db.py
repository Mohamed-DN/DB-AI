import pymongo
from pprint import pprint

try:
    # Connect
    client = pymongo.MongoClient("mongodb://admin:nexi2024@localhost:28017/?authSource=admin")
    
    print("--- Listing Databases ---")
    print(client.list_database_names())
    
    db_v2 = client["nexi_cmdb_v2"]
    print("\n--- CONTENT OF nexi_cmdb_v2.oem_instances ---")
    instances = list(db_v2.oem_instances.find())
    pprint(instances)
    
    print("\n--- CONTENT OF nexi_cmdb_v2.databases (first 3) ---")
    dbs = list(db_v2.databases.find().limit(3))
    pprint(dbs)
    
except Exception as e:
    print(e)
