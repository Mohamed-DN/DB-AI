
from pymongo import MongoClient
import sys

def test_conn(host, port, user=None, pwd=None):
    if user:
        uri = f"mongodb://{user}:{pwd}@{host}:{port}/?authSource=admin"
    else:
        uri = f"mongodb://{host}:{port}/"
    
    print(f"Testing {uri}...")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        dbs = client.list_database_names()
        print(f"✅ Success! Databases: {dbs}")
        return client, dbs
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None, None

def main():
    ports = [27017, 28017]
    creds = [
        ("admin", "nexi2024"),
        (None, None)
    ]
    
    for port in ports:
        for user, pwd in creds:
            client, dbs = test_conn("127.0.0.1", port, user, pwd)
            if client:
                for db_name in ["nexi_cmdb_v2", "nexi_cmdb"]:
                    if db_name in dbs:
                        print(f"   ⭐ FOUND DATA IN {db_name} on port {port}")

if __name__ == "__main__":
    main()
