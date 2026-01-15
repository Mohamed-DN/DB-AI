import sys
import os
import subprocess
sys.path.append(os.getcwd())
from Orchestrator.src.mongo_proxy import MongoProxy

def get_all_docker_ids():
    """Get all container IDs (running and stopped)"""
    try:
        # Get long IDs
        res = subprocess.check_output(["docker", "ps", "-a", "--format", "{{.ID}}"]).decode().split()
        # Also get names just in case
        res_names = subprocess.check_output(["docker", "ps", "-a", "--format", "{{.Names}}"]).decode().split()
        return set(res + res_names)
    except:
        return set()

try:
    m = MongoProxy()
    all_ids = get_all_docker_ids()
    print(f"Found {len(all_ids)} docker artifacts.")

    # Get inventory
    dbs = m.execute_eval("db.inventory_databases.find({ 'connection.type': 'DOCKER' }).toArray()")
    
    deleted = 0
    for db in dbs:
        # Check by container ID if present in connection or metrics (not standard field, checking map)
        # Actually standard is 'connection.container' which is usually NAME.
        # But UI shows ID? Maybe UI matches it?
        # Screenshot shows ID.
        # Let's check connection.container.
        container_ref = db.get('connection', {}).get('container')
        
        if not container_ref:
            continue
            
        # If the container NAME or ID does not exist in docker ps -a, it's a ghost.
        # We need to be careful. 'nexi-cmdb-mongo' is a name. 'cb50...' is an ID.
        # all_ids has both.
        
        # Check if we should delete
        if container_ref not in all_ids:
            # Maybe it's a short ID?
            # container_ref might be "nexi-pg-milano-dev".
            # If that name is not in all_ids, then it's gone?
            pass 
            
            # Let's act conservatively.
            # If we see multiple entries for same 'db_unique_name'?
            # The screenshot shows "nexi-pg-milano" twice. 
            # Implies they might have DIFFERENT db_unique_names? Or same?
            # If same, MongoProxy upsert should have merged them.
            # So they must have different `db_unique_name`? 
            # Or duplicate docs?
            
            # Let's check duplicates by name first.
            name = db.get('identity', {}).get('db_unique_name')
            
            # If we find a db whose container reference is totally missing from docker, delete it.
            print(f"Checking {name} ({container_ref})...")
            
            # Fuzzy match for ID (if container_ref is short ID)
            match = False
            for real_id in all_ids:
                if real_id.startswith(container_ref) or container_ref.startswith(real_id):
                    match = True
                    break
            
            if not match:
                print(f"❌ Container {container_ref} for {name} not found in Docker. Deleting...")
                m.execute_eval(f"db.inventory_databases.deleteOne({{ _id: ObjectId('{db['_id']}') }})")
                deleted += 1

    print(f"Cleanup complete. Removed {deleted} ghosts.")

except Exception as e:
    print(f"Error: {e}")
