#!/usr/bin/env python3
"""
Discover Docker databases (PostgreSQL, Oracle) and output as JSON.
Part of the 3-layer architecture - Execution layer.
"""
import subprocess
import json
import sys

def get_docker_containers():
    """List running Docker containers"""
    cmd = ["docker", "ps", "--format", "{{.Names}}\t{{.Image}}\t{{.Status}}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return []
    
    containers = []
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) >= 3:
            containers.append({
                "name": parts[0],
                "image": parts[1],
                "status": parts[2]
            })
    return containers

def identify_database_type(container):
    """Identify if container is a database and what type"""
    name = container["name"].lower()
    image = container["image"].lower()
    
    if "postgres" in image or "pg" in name:
        return "POSTGRES"
    elif "oracle" in image or "oracle" in name:
        return "ORACLE"
    elif "mongo" in image:
        return "MONGODB"
    return None

def check_database_health(container_name, db_type):
    """Check if database is responsive"""
    if db_type == "POSTGRES":
        cmd = ["docker", "exec", container_name, "pg_isready", "-U", "postgres"]
    elif db_type == "ORACLE":
        # Simple check - try to run sqlplus
        cmd = ["docker", "exec", container_name, "sqlplus", "-V"]
    else:
        return "UNKNOWN"
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return "UP" if result.returncode == 0 else "DOWN"

def discover_databases():
    """Main discovery function"""
    containers = get_docker_containers()
    databases = []
    
    for container in containers:
        db_type = identify_database_type(container)
        if db_type and db_type != "MONGODB":  # Skip MongoDB (it's our CMDB)
            status = "UP" if "Up" in container["status"] else "DOWN"
            
            databases.append({
                "identity": {
                    "db_unique_name": container["name"].upper().replace("-", "_"),
                    "engine": db_type,
                    "topology": "STANDALONE",
                    "environment": "DOCKER_LAB"
                },
                "connection": {
                    "container": container["name"],
                    "type": "DOCKER"
                },
                "state": {
                    "status": status,
                    "last_seen": None  # Will be set by register script
                }
            })
    
    return databases

if __name__ == "__main__":
    databases = discover_databases()
    print(json.dumps(databases, indent=2))
