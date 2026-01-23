from pymongo import MongoClient
import os
from pprint import pprint

# Connect to MongoDB
client = MongoClient('localhost', 28017, username='admin', password='nexi2024', authSource='admin')
db = client.nexi_cmdb_v2
collection = db.inventory_databases

# Write to file
with open("inventory_report.txt", "w", encoding="utf-8") as f:
    f.write(f"Total Documents: {collection.count_documents({})}\n")

    # 1. Check for duplicates by unique_name
    pipeline = [
        {'$group': {
            '_id': '$identity.db_unique_name', 
            'count': {'$sum': 1}, 
            'ids': {'$push': '$_id'},
            'statuses': {'$push': '$state.status'}
        }},
        {'$match': {'count': {'$gt': 1}}}
    ]
    duplicates = list(collection.aggregate(pipeline))

    if duplicates:
        f.write("\n⚠️  DUPLICATES FOUND:\n")
        for d in duplicates:
            f.write(f"Name: {d['_id']} - Count: {d['count']} - Statuses: {d['statuses']}\n")
    else:
        f.write("\n✅ No strict duplicates by db_unique_name found.\n")

    # 2. List all databases to see potential "similar" ones or "ghosts"
    f.write("\n📋  FULL DATABASE LIST:\n")
    all_dbs = collection.find({}, {'identity.db_unique_name': 1, 'identity.engine': 1, 'state.status': 1, 'connection.host': 1})
    for db_doc in all_dbs:
        ident = db_doc.get('identity', {})
        name = ident.get('db_unique_name', 'N/A')
        engine = ident.get('engine', 'N/A')
        status = db_doc.get('state', {}).get('status', 'UNKNOWN')
        host = db_doc.get('connection', {}).get('host', 'N/A')
        f.write(f" - {name:<30} | {engine:<10} | {status:<10} | {host}\n")

