#!/usr/bin/env python3
"""
Register a database in MongoDB CMDB.
Part of the 3-layer architecture - Execution layer.

Usage:
    python register_database.py '{"identity": {...}, "connection": {...}, "state": {...}}'
    OR
    echo '...' | python register_database.py
"""
import subprocess
import json
import sys
from datetime import datetime

# MongoDB configuration (from directive learnings)
MONGO_CONTAINER = "m-dn-cmdb-mongo"
MONGO_USER = "admin"
MONGO_PASS = "admin123"
MONGO_DB = "m-dn_cmdb"
MONGO_COLLECTION = "inventory_databases"

def execute_mongo_command(js_command):
    """Execute a mongosh command and return result"""
    cmd = [
        "docker", "exec", MONGO_CONTAINER,
        "mongosh", MONGO_DB,
        "--username", MONGO_USER,
        "--password", MONGO_PASS,
        "--authenticationDatabase", "admin",
        "--quiet",
        "--eval", js_command
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return None
    return result.stdout.strip()

def register_database(db_data):
    """Register or update a database in MongoDB"""
    # Add timestamp
    db_data["state"]["last_seen"] = datetime.utcnow().isoformat() + "Z"
    
    db_name = db_data["identity"]["db_unique_name"]
    
    # Upsert command
    js_cmd = f"""
    db.{MONGO_COLLECTION}.updateOne(
        {{ "identity.db_unique_name": "{db_name}" }},
        {{ $set: {json.dumps(db_data)} }},
        {{ upsert: true }}
    )
    """
    
    result = execute_mongo_command(js_cmd)
    if result:
        print(f"[OK] Registered: {db_name}")
        return True
    else:
        print(f"[FAIL] Failed: {db_name}", file=sys.stderr)
        return False

def main():
    # Read input from stdin or args
    if len(sys.argv) > 1:
        data = sys.argv[1]
    else:
        data = sys.stdin.read()
    
    try:
        databases = json.loads(data)
        
        # Handle both single object and array
        if isinstance(databases, dict):
            databases = [databases]
        
        success = 0
        for db in databases:
            if register_database(db):
                success += 1
        
        print(f"\nRegistered {success}/{len(databases)} databases")
        return 0 if success == len(databases) else 1
        
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
