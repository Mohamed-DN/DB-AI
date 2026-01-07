"""
Create AIAUTO user on ALL databases with FULL GRANTS
- PostgreSQL (Docker): aiauto with SUPERUSER
- Oracle Docker (Cairo): c##aiauto with DBA
- Oracle RAC (VirtualBox): c##aiauto on CDB, aiauto on PDBs
"""
import sys
import os
import subprocess

# Force UTF-8 for Windows Console
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("AIAUTO USER CREATION - Full Grants on ALL Databases")
print("=" * 70)

# ============================================================================
# POSTGRESQL (Docker Containers)
# ============================================================================
pg_containers = [
    "nexi-pg-milano-prod",
    "nexi-pg-milano-dev", 
    "nexi-pg-milano-stg",
    "nexi-pg-bratislava-prod",
    "nexi-pg-bratislava-dev"
]

print("\n[PostgreSQL - Docker Containers]")
for container in pg_containers:
    print(f"\n  {container}:")
    try:
        # Drop user if exists (to reset), then create with full grants
        cmds = [
            f'docker exec {container} psql -U postgres -c "DROP USER IF EXISTS aiauto;"',
            f'docker exec {container} psql -U postgres -c "CREATE USER aiauto WITH PASSWORD \'root\' SUPERUSER CREATEDB CREATEROLE LOGIN;"',
            f'docker exec {container} psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE postgres TO aiauto;"',
        ]
        for cmd in cmds:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # Verify
        verify = subprocess.run(
            f'docker exec {container} psql -U postgres -tAc "SELECT rolsuper FROM pg_roles WHERE rolname=\'aiauto\'"',
            shell=True, capture_output=True, text=True
        )
        if verify.stdout.strip() == 't':
            print("    ✅ AIAUTO created with SUPERUSER")
        else:
            print(f"    ⚠️ Check manually: {verify.stderr}")
                
    except Exception as e:
        print(f"    ❌ Error: {e}")

# ============================================================================
# ORACLE DOCKER (Cairo Containers)
# ============================================================================
oracle_containers = [
    "nexi-oracle-cairo-primary",
    "nexi-oracle-cairo-replica"
]

print("\n[Oracle - Docker Containers (Cairo)]")
for container in oracle_containers:
    print(f"\n  {container}:")
    try:
        # Check if container is running
        check = subprocess.run(f'docker inspect {container} --format "{{{{.State.Running}}}}"', 
                               shell=True, capture_output=True, text=True)
        if check.stdout.strip() != 'true':
            print(f"    ⚠️ Container not running")
            continue
            
        # Create user via sqlplus
        sql = '''
DROP USER c##aiauto CASCADE;
CREATE USER c##aiauto IDENTIFIED BY root CONTAINER=ALL;
GRANT DBA TO c##aiauto CONTAINER=ALL;
GRANT CONNECT, RESOURCE TO c##aiauto CONTAINER=ALL;
GRANT SELECT ANY TABLE TO c##aiauto CONTAINER=ALL;
GRANT SELECT ANY DICTIONARY TO c##aiauto CONTAINER=ALL;
COMMIT;
EXIT;
'''
        # Write SQL to temp file
        sql_file = f'/tmp/create_aiauto_{container}.sql'
        subprocess.run(f'docker exec {container} bash -c "echo \'{sql}\' > {sql_file}"', shell=True)
        
        # Execute
        result = subprocess.run(
            f'docker exec {container} sqlplus -S sys/nexi2024 as sysdba @{sql_file}',
            shell=True, capture_output=True, text=True, timeout=30
        )
        
        if 'ORA-01918' in result.stdout or 'User created' in result.stdout or 'Grant succeeded' in result.stdout:
            print("    ✅ C##AIAUTO created with DBA grants")
        else:
            print(f"    ⚠️ Output: {result.stdout[:200]}")
                
    except subprocess.TimeoutExpired:
        print(f"    ⚠️ Timeout - container may be starting up")
    except Exception as e:
        print(f"    ❌ Error: {e}")

# ============================================================================
# ORACLE RAC (VirtualBox - Remote via oracledb)
# ============================================================================
print("\n[Oracle - VirtualBox RAC]")

try:
    import oracledb
    
    rac_hosts = [
        {"host": "192.168.56.101", "service": "cdbrac"},
        {"host": "192.168.56.102", "service": "cdbrac"}
    ]
    
    for rac in rac_hosts:
        print(f"\n  {rac['host']}:")
        try:
            conn = oracledb.connect(
                user="sys",
                password="root", 
                dsn=f"{rac['host']}:1521/{rac['service']}",
                mode=oracledb.AUTH_MODE_SYSDBA
            )
            cursor = conn.cursor()
            
            # Create C##AIAUTO on CDB
            try:
                cursor.execute("DROP USER C##AIAUTO CASCADE")
            except:
                pass
            
            try:
                cursor.execute("CREATE USER C##AIAUTO IDENTIFIED BY root CONTAINER=ALL")
                cursor.execute("GRANT DBA TO C##AIAUTO CONTAINER=ALL")
                cursor.execute("GRANT CONNECT, RESOURCE TO C##AIAUTO CONTAINER=ALL")
                cursor.execute("GRANT SELECT ANY TABLE TO C##AIAUTO CONTAINER=ALL")
                cursor.execute("GRANT SELECT ANY DICTIONARY TO C##AIAUTO CONTAINER=ALL")
                print("    ✅ C##AIAUTO created on CDB with DBA grants")
            except oracledb.DatabaseError as e:
                print(f"    ⚠️ CDB: {e}")
            
            # Create AIAUTO in each PDB
            for pdb in ["PDB1", "SOLE", "LUNA"]:
                try:
                    cursor.execute(f"ALTER SESSION SET CONTAINER = {pdb}")
                    try:
                        cursor.execute("DROP USER AIAUTO CASCADE")
                    except:
                        pass
                    cursor.execute("CREATE USER AIAUTO IDENTIFIED BY root")
                    cursor.execute("GRANT DBA TO AIAUTO")
                    cursor.execute("GRANT CONNECT, RESOURCE TO AIAUTO")
                    cursor.execute("GRANT SELECT ANY TABLE TO AIAUTO")
                    cursor.execute("GRANT SELECT ANY DICTIONARY TO AIAUTO")
                    print(f"    ✅ AIAUTO created in {pdb}")
                except oracledb.DatabaseError as e:
                    if "ORA-01109" in str(e):
                        print(f"    ⚠️ {pdb}: Not open")
                    else:
                        print(f"    ⚠️ {pdb}: {e}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"    ❌ Connection failed: {e}")
            
except ImportError:
    print("  ⚠️ oracledb module not available")

print("\n" + "=" * 70)
print("AIAUTO User Creation Complete!")
print("=" * 70)
print("\nCredentials Summary:")
print("  PostgreSQL: aiauto / root (SUPERUSER)")
print("  Oracle CDB: c##aiauto / root (DBA)")
print("  Oracle PDB: aiauto / root (DBA)")
print("\nConnection Examples:")
print("  psql -h 127.0.0.1 -p 5432 -U aiauto -d postgres")
print("  sqlplus c##aiauto/root@//192.168.56.101:1521/cdbrac")
print("  sqlplus aiauto/root@//192.168.56.101:1521/pdb1")
