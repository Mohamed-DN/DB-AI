
import pymongo
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["nexi_cmdb_v2"]
print(f"Collections: {db.list_collection_names()}")
for col in db.list_collection_names():
    count = db[col].count_documents({})
    print(f" - {col}: {count}")
    if count > 0:
        for doc in db[col].find().limit(1):
            doc.pop("_id", None)
            print(f"   Example: {doc}")
