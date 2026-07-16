
import sys
import os
import requests
import time
from pymongo import MongoClient
import redis

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def check_backend():
    url = "http://localhost:8000/"
    print(f"Testing Backend: {url} ... ", end="")
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            print("✅ UP")
            return True
        else:
            print(f"❌ DOWN ({r.status_code})")
            return False
    except Exception as e:
        print(f"❌ DOWN ({e})")
        return False

def check_frontend():
    url = "http://localhost:4002"
    print(f"Testing Frontend: {url} ... ", end="")
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            print("✅ UP")
            return True
        else:
            print(f"❌ DOWN ({r.status_code})")
            return False
    except Exception as e:
        print(f"❌ DOWN ({e})")
        return False

def check_mongo():
    uri = "mongodb://admin:pippopippo_1234@localhost:28017/"
    print(f"Testing MongoDB: {uri} ... ", end="")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        client.server_info()
        print("✅ UP")
        return True
    except Exception as e:
        print(f"❌ DOWN ({e})")
        return False

def check_redis():
    host = "localhost"
    port = 7379
    print(f"Testing Redis: {host}:{port} ... ", end="")
    try:
        r = redis.Redis(host=host, port=port, password="pippopippo_1234", socket_timeout=2)
        r.ping()
        print("✅ UP")
        return True
    except Exception as e:
        print(f"❌ DOWN ({e})")
        return False

def main():
    print("=== SYSTEM VERIFICATION ===")
    backend = check_backend()
    frontend = check_frontend()
    mongo = check_mongo()
    redis_status = check_redis()
    
    if all([backend, frontend, mongo, redis_status]):
        print("\n✅ INITIAL SYSTEM CHECK PASSED!")
    else:
        print("\n❌ SYSTEM CHECK FAILED - See details above.")
        
if __name__ == "__main__":
    main()
