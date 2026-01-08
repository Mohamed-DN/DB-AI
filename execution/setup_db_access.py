#!/usr/bin/env python3
"""
Setup Database Access for NEXI CMDB
===================================
Creates users and configures access for:
1. PostgreSQL: aiauto user + pg_hba.conf entries
2. Oracle Docker: c##aiauto user with grants
3. Oracle VirtualBox: Instructions for manual setup (requires VBox VMs running)
"""

import subprocess
import sys

# PostgreSQL containers and their ports
PG_CONTAINERS = [
    "nexi-pg-milano-prod",
    "nexi-pg-milano-stg", 
    "nexi-pg-milano-dev",
    "nexi-pg-bratislava-prod",
    "nexi-pg-bratislava-dev",
]

# Oracle Docker containers
ORACLE_CONTAINERS = [
    "nexi-oracle-cairo-primary",
    "nexi-oracle-cairo-replica",
]

def run_docker_exec(container: str, command: str, user: str = None) -> tuple:
    """Execute command in Docker container"""
    cmd = ["docker", "exec"]
    if user:
        cmd.extend(["-u", user])
    cmd.extend([container, "bash", "-c", command])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)

def setup_postgres_user(container: str):
    """Create aiauto user in PostgreSQL with full access"""
    print(f"\n[PG] Setting up aiauto user in {container}...")
    
    # Create user and grant privileges
    sql_commands = """
    -- Create user if not exists
    DO \\$\\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'aiauto') THEN
            CREATE USER aiauto WITH PASSWORD 'root' SUPERUSER CREATEDB CREATEROLE;
            RAISE NOTICE 'User aiauto created';
        ELSE
            ALTER USER aiauto WITH PASSWORD 'root' SUPERUSER;
            RAISE NOTICE 'User aiauto updated';
        END IF;
    END
    \\$\\$;
    
    -- Grant all privileges
    GRANT ALL PRIVILEGES ON DATABASE postgres TO aiauto;
    """
    
    success, output = run_docker_exec(container, f'psql -U postgres -c "{sql_commands}"')
    if success:
        print(f"    [OK] User aiauto configured")
    else:
        print(f"    [ERROR] {output}")
    
    return success

def setup_postgres_hba(container: str):
    """Configure pg_hba.conf to allow connections from Docker network"""
    print(f"[PG] Configuring pg_hba.conf in {container}...")
    
    # Add entries for Docker network ranges
    hba_entries = """
# NEXI CMDB Access - Added by setup script
host    all             aiauto          0.0.0.0/0               md5
host    all             aiauto          172.16.0.0/12           md5
host    all             aiauto          192.168.0.0/16          md5
host    all             all             samenet                 md5
"""
    
    # Find pg_hba.conf location and append entries
    find_cmd = "find /var/lib/postgresql -name 'pg_hba.conf' 2>/dev/null | head -1"
    success, hba_path = run_docker_exec(container, find_cmd)
    hba_path = hba_path.strip()
    
    if not hba_path:
        # Try common locations
        hba_path = "/var/lib/postgresql/data/pg_hba.conf"
    
    # Check if entries already exist
    check_cmd = f"grep -q 'NEXI CMDB Access' {hba_path} && echo 'exists' || echo 'missing'"
    _, check_result = run_docker_exec(container, check_cmd)
    
    if "exists" in check_result:
        print(f"    [OK] pg_hba.conf already configured")
        return True
    
    # Append new entries
    append_cmd = f"echo '{hba_entries}' >> {hba_path}"
    success, output = run_docker_exec(container, append_cmd)
    
    if success:
        # Reload PostgreSQL config
        reload_cmd = "su - postgres -c 'pg_ctl reload -D /var/lib/postgresql/data' 2>/dev/null || psql -U postgres -c 'SELECT pg_reload_conf();'"
        run_docker_exec(container, reload_cmd)
        print(f"    [OK] pg_hba.conf updated and reloaded")
    else:
        print(f"    [ERROR] Failed to update pg_hba.conf: {output}")
    
    return success

def setup_oracle_user(container: str):
    """Create c##aiauto user in Oracle with DBA privileges"""
    print(f"\n[ORACLE] Setting up c##aiauto user in {container}...")
    
    # SQL to create common user with grants
    sql_commands = """
-- Enable script output
SET SERVEROUTPUT ON;

-- Create common user if not exists
DECLARE
    user_exists NUMBER;
BEGIN
    SELECT COUNT(*) INTO user_exists FROM dba_users WHERE username = 'C##AIAUTO';
    IF user_exists = 0 THEN
        EXECUTE IMMEDIATE 'CREATE USER c##aiauto IDENTIFIED BY root CONTAINER=ALL';
        DBMS_OUTPUT.PUT_LINE('User c##aiauto created');
    ELSE
        EXECUTE IMMEDIATE 'ALTER USER c##aiauto IDENTIFIED BY root';
        DBMS_OUTPUT.PUT_LINE('User c##aiauto password updated');
    END IF;
END;
/

-- Grant privileges
GRANT CONNECT, RESOURCE, DBA TO c##aiauto CONTAINER=ALL;
GRANT CREATE SESSION TO c##aiauto CONTAINER=ALL;
GRANT SELECT ANY DICTIONARY TO c##aiauto CONTAINER=ALL;
GRANT SELECT ON V_\\$SESSION TO c##aiauto CONTAINER=ALL;
GRANT SELECT ON V_\\$DATABASE TO c##aiauto CONTAINER=ALL;

-- Also create local aiauto user for PDB connections
DECLARE
    user_exists NUMBER;
BEGIN
    SELECT COUNT(*) INTO user_exists FROM dba_users WHERE username = 'AIAUTO';
    IF user_exists = 0 THEN
        EXECUTE IMMEDIATE 'CREATE USER aiauto IDENTIFIED BY root';
        DBMS_OUTPUT.PUT_LINE('User aiauto created');
    ELSE
        EXECUTE IMMEDIATE 'ALTER USER aiauto IDENTIFIED BY root';
        DBMS_OUTPUT.PUT_LINE('User aiauto password updated');
    END IF;
END;
/

GRANT CONNECT, RESOURCE, DBA TO aiauto;
GRANT CREATE SESSION TO aiauto;

EXIT;
"""
    
    # Write SQL to temp file and execute
    write_cmd = f"echo \"{sql_commands}\" > /tmp/setup_aiauto.sql"
    run_docker_exec(container, write_cmd)
    
    # Execute as oracle user
    exec_cmd = "sqlplus -S / as sysdba @/tmp/setup_aiauto.sql"
    success, output = run_docker_exec(container, exec_cmd)
    
    if "created" in output.lower() or "updated" in output.lower() or "grant succeeded" in output.lower():
        print(f"    [OK] User c##aiauto and aiauto configured")
        success = True
    else:
        print(f"    [WARN] Check output: {output[:200]}")
    
    return success

def check_vbox_connectivity():
    """Check if VirtualBox Oracle RAC is reachable"""
    print("\n[VBOX] Checking VirtualBox Oracle RAC connectivity...")
    
    # Try to ping from gateway container
    for host in ["192.168.56.101", "192.168.56.102"]:
        cmd = f"docker exec maesdn-gateway ping -c 1 -W 2 {host} 2>/dev/null"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"    [OK] {host} is reachable from gateway")
            else:
                print(f"    [WARN] {host} not reachable - VirtualBox VMs may be off")
        except:
            print(f"    [WARN] Could not check {host}")

def print_vbox_instructions():
    """Print instructions for VirtualBox Oracle RAC setup"""
    print("""
================================================================================
MANUAL STEPS REQUIRED FOR VIRTUALBOX ORACLE RAC
================================================================================

The VirtualBox Oracle RAC (192.168.56.101/102) requires manual configuration:

1. START THE VMs:
   - Open VirtualBox Manager
   - Start rac1 and rac2 VMs
   - Wait for Oracle to start (~2-3 minutes)

2. CREATE THE AIAUTO USER (run on rac1 as oracle):
   
   sqlplus / as sysdba
   
   -- In CDB:
   CREATE USER c##aiauto IDENTIFIED BY root CONTAINER=ALL;
   GRANT CONNECT, RESOURCE, DBA TO c##aiauto CONTAINER=ALL;
   GRANT CREATE SESSION TO c##aiauto CONTAINER=ALL;
   
   -- In each PDB (PDB1, SOLE, LUNA):
   ALTER SESSION SET CONTAINER=PDB1;
   CREATE USER aiauto IDENTIFIED BY root;
   GRANT CONNECT, RESOURCE, DBA TO aiauto;
   
   ALTER SESSION SET CONTAINER=SOLE;
   CREATE USER aiauto IDENTIFIED BY root;
   GRANT CONNECT, RESOURCE, DBA TO aiauto;
   
   ALTER SESSION SET CONTAINER=LUNA;
   CREATE USER aiauto IDENTIFIED BY root;
   GRANT CONNECT, RESOURCE, DBA TO aiauto;

3. VERIFY LISTENER:
   lsnrctl status
   
   Ensure listener is running and services are registered.

4. NETWORK ROUTING (if Docker can't reach VBox):
   On Windows host, ensure VirtualBox Host-Only network is configured:
   - IP: 192.168.56.1
   - Subnet: 255.255.255.0
   
   Docker containers may need routing setup to reach 192.168.56.x network.
   Consider adding a route or using port forwarding.

================================================================================
""")

def main():
    print("=" * 60)
    print("NEXI CMDB - Database Access Setup")
    print("=" * 60)
    
    # Setup PostgreSQL containers
    print("\n--- PostgreSQL Setup ---")
    for container in PG_CONTAINERS:
        # Check if container is running
        check_cmd = f"docker ps --filter name={container} --filter status=running -q"
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        if result.stdout.strip():
            setup_postgres_user(container)
            setup_postgres_hba(container)
        else:
            print(f"[SKIP] {container} is not running")
    
    # Setup Oracle Docker containers
    print("\n--- Oracle Docker Setup ---")
    for container in ORACLE_CONTAINERS:
        check_cmd = f"docker ps --filter name={container} --filter status=running -q"
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        if result.stdout.strip():
            setup_oracle_user(container)
        else:
            print(f"[SKIP] {container} is not running")
    
    # Check VirtualBox connectivity
    check_vbox_connectivity()
    
    # Print VirtualBox instructions
    print_vbox_instructions()
    
    print("\n[DONE] Setup complete!")
    print("Restart containers if pg_hba.conf was modified:")
    print("  docker-compose -f docker-lab/docker-compose.yml restart")

if __name__ == "__main__":
    main()
