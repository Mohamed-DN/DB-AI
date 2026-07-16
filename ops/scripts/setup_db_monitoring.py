"""
Setup Monitoring Users
Creates 'checkmk' user with limited privileges on all Database containers.
"""
import subprocess
import os

def run_docker_exec(container, cmd):
    try:
        full_cmd = ["docker", "exec", "-i", container] + cmd
        res = subprocess.run(full_cmd, capture_output=True, text=True, timeout=30)
        return res.returncode == 0, res.stdout, res.stderr
    except Exception as e:
        return False, "", str(e)

def setup_postgres(container, password="monitor_pass"):
    print(f"🔧 Configuring PostgreSQL: {container}")
    
    # Create User
    sql_create_user = f"CREATE USER checkmk WITH PASSWORD '{password}';"
    sql_grant = "GRANT SELECT ON pg_stat_database TO checkmk;"
    # Allow connection limits viewing
    sql_grant_2 = "GRANT SELECT ON pg_stat_activity TO checkmk;"

    cmd = ["psql", "-U", "postgres", "-c", sql_create_user]
    ok, out, err = run_docker_exec(container, cmd)
    if "already exists" in err:
        print(f"  - User exists.")
    elif not ok:
        print(f"  - Error creating user: {err}")
    else:
        print(f"  - User created.")

    cmd = ["psql", "-U", "postgres", "-c", sql_grant]
    run_docker_exec(container, cmd)
    cmd = ["psql", "-U", "postgres", "-c", sql_grant_2]
    run_docker_exec(container, cmd)

def setup_oracle(container, password="monitor_pass"):
    print(f"🔧 Configuring Oracle: {container}")
    
    # Oracle requires sysdba to create users usually
    sql_script = f"""
    ALTER SESSION SET "_ORACLE_SCRIPT"=true;
    CREATE USER checkmk IDENTIFIED BY {password};
    GRANT CONNECT, RESOURCE TO checkmk;
    GRANT SELECT ANY DICTIONARY TO checkmk;
    GRANT SELECT ON V_$SESSION TO checkmk;
    GRANT SELECT ON V_$SYSSTAT TO checkmk;
    GRANT SELECT ON V_$RESOURCE_LIMIT TO checkmk;
    EXIT;
    """
    
    cmd = ["sqlplus", "-s", "/ as sysdba"]
    
    try:
        # Pass script via stdin
        full_cmd = ["docker", "exec", "-i", container, "sqlplus", "-s", "/ as sysdba"]
        res = subprocess.run(full_cmd, input=sql_script, capture_output=True, text=True, timeout=30)
        if "ORA-01920" in res.stdout: # User name conflicts
            print(f"  - User exists.")
        elif res.returncode != 0:
             print(f"  - Error: {res.stdout}")
        else:
             print(f"  - User created & Grants given.")
    except Exception as e:
        print(f"  - Exec failed: {e}")

def main():
    suffix = os.getenv('GATEWAY_SUFFIX', '2')
    
    pg_containers = [
        f"m-dn-pg-milano-prod{suffix}",
        f"m-dn-pg-milano-dev{suffix}",
        f"m-dn-bratislava-prod{suffix}", # Error in parsing potential name in mind? checking list
        f"m-dn-pg-bratislava-prod{suffix}",
        f"m-dn-pg-bratislava-dev{suffix}"
    ]
    
    ora_containers = [
        f"m-dn-oracle-cairo-primary{suffix}",
        f"m-dn-oracle-cairo-replica{suffix}"
    ]

    print("🚀 Starting DB Monitoring Setup...")
    
    for c in pg_containers:
        # Check if container running
        res = subprocess.run(["docker", "inspect", c], capture_output=True)
        if res.returncode == 0:
            setup_postgres(c)
        else:
            print(f"⚠️ Container {c} not found/running")

    for c in ora_containers:
        res = subprocess.run(["docker", "inspect", c], capture_output=True)
        if res.returncode == 0:
            setup_oracle(c)
        else:
             print(f"⚠️ Container {c} not found/running")

if __name__ == "__main__":
    main()
