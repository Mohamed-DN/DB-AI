from pymongo import MongoClient
import sys

try:
    print("Testing URI connection...")
    uri = "mongodb://admin:nexi2024@127.0.0.1:27017/?authSource=admin"
    client = MongoClient(uri)
    print(client.list_database_names())
    print("URI Success!")
except Exception as e:
    print(f"URI Failed: {e}")

try:
    print("\nTesting Args connection...")
    client = MongoClient(host='127.0.0.1', port=27017, username='admin', password='nexi2024', authSource='admin')
    print(client.list_database_names())
    print("Args Success!")
except Exception as e:
    print(f"Args Failed: {e}")
