
import os
import sys
import argparse
import tempfile
import subprocess
from pymongo import MongoClient

# Add root path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Connection details
MONGO_HOST = os.getenv("MONGODB_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGODB_PORT", "27017"))
MONGO_USER = os.getenv("MONGO_USERNAME", "admin")
MONGO_PASS = os.getenv("MONGO_PASSWORD", "nexi2024")
MONGO_DB = os.getenv("MONGODB_DB", "nexi_cmdb_v2")

def get_script_content(script_name):
    # Ensure extension
    if not script_name.endswith(".py"):
        script_name += ".py"
        
    uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
    client = MongoClient(uri)
    db = client[MONGO_DB]
    collection = db["system_scripts"]
    
    doc = collection.find_one({"name": script_name})
    if not doc:
        print(f"❌ Script '{script_name}' not found in MongoDB.")
        return None
    
    return doc.get("content")

def run_script(script_name, args):
    content = get_script_content(script_name)
    if not content:
        sys.exit(1)
        
    print(f"🚀 Fetching '{script_name}' from MongoDB...")
    
    # Write to a temp file IN THE OPS/SCRIPTS DIRECTORY to preserve import relativity
    # We use the current directory (ops/scripts) as the base
    base_dir = os.path.dirname(os.path.abspath(__file__))
    temp_name = f"mongo_exec_{script_name}"
    if not temp_name.endswith(".py"):
        temp_name += ".py"
        
    temp_path = os.path.join(base_dir, temp_name)
    
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"✅ Loaded. Executing...")
        
        # Build command
        cmd = [sys.executable, temp_path] + args
        
        # execution
        subprocess.run(cmd, check=False)
        
    except Exception as e:
        print(f"❌ Execution failed: {e}")
    finally:
        # Cleanup
        if os.path.exists(temp_path):
             try:
                 os.remove(temp_path)
             except:
                 pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run scripts stored in MongoDB")
    parser.add_argument("script", help="Name of the script to run (e.g. verify_system.py)")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for the script")
    
    args = parser.parse_args()
    
    # Handle the case where argparse swallows the script args
    # simple usage: python mongo_runner.py my_script.py --arg1 val1
    
    run_script(args.script, args.args)
