from pymongo import MongoClient
try:
    print("Testing DBA User connection with DirectConnection...")
    # client = MongoClient("mongodb://dba:dba@127.0.0.1:27017/nexi_cmdb?directConnection=true")
    client = MongoClient(host='127.0.0.1', port=27017, username='dba', password='dba', authSource='nexi_cmdb', directConnection=True)
    print(client.nexi_cmdb.list_collection_names())
    print("DBA Success!")
except Exception as e:
    print(f"DBA Failed: {e}")
