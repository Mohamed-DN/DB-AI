"""
UserProvisioner Agent - Creates service accounts for AI monitoring
================================================================
Creates:
- Oracle: C##AIAUTO (CDB) or AIAUTO (PDB) with DBA grants
- PostgreSQL: aiauto with SUPERUSER grants

These accounts are used by the Enricher agent to collect metadata.
"""
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, Optional

# Force UTF-8 for Windows Console
sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from orchestrator.core.mongo_proxy import MongoProxy

# Database libraries
try:
    import oracledb
    ORACLEDB_AVAILABLE = True
except ImportError:
    ORACLEDB_AVAILABLE = False
    print("[WARN] oracledb not available")

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("[WARN] psycopg2 not available")


class OracleUserProvisioner:
    """Creates monitoring user on Oracle databases"""
    
    # Default password for AI service account
    AI_USER_PASSWORD = os.getenv("AIAUTO_PASSWORD", "root")
    
    def __init__(self, host: str, port: int, service_name: str, 
                 sys_user: str = "sys", sys_password: str = "root"):
        self.host = host
        self.port = port
        self.service_name = service_name
        self.sys_user = sys_user
        self.sys_password = sys_password
    
    def connect_as_sysdba(self):
        """Connect to Oracle as SYSDBA"""
        if not ORACLEDB_AVAILABLE:
            raise Exception("oracledb not available")
        
        dsn = f"{self.host}:{self.port}/{self.service_name}"
        return oracledb.connect(
            user=self.sys_user,
            password=self.sys_password,
            dsn=dsn,
            mode=oracledb.AUTH_MODE_SYSDBA
        )
    
    def is_cdb(self, conn) -> bool:
        """Check if database is a CDB"""
        cursor = conn.cursor()
        cursor.execute("SELECT CDB FROM V$DATABASE")
        return cursor.fetchone()[0] == "YES"
    
    def user_exists(self, conn, username: str) -> bool:
        """Check if user exists"""
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM DBA_USERS WHERE USERNAME = UPPER('{username}')")
        return cursor.fetchone()[0] > 0
    
    def create_user_cdb(self, conn):
        """Create C##AIAUTO user in CDB (common user)"""
        username = "C##AIAUTO"
        cursor = conn.cursor()
        
        if self.user_exists(conn, username):
            print(f"   ⏭️ User {username} already exists")
            return True
        
        try:
            # Create common user
            cursor.execute(f"""
                CREATE USER {username} IDENTIFIED BY "{self.AI_USER_PASSWORD}"
                DEFAULT TABLESPACE USERS
                TEMPORARY TABLESPACE TEMP
                CONTAINER=ALL
            """)
            
            # Grant privileges
            cursor.execute(f"GRANT DBA TO {username} CONTAINER=ALL")
            cursor.execute(f"GRANT SELECT ANY DICTIONARY TO {username} CONTAINER=ALL")
            cursor.execute(f"GRANT SELECT_CATALOG_ROLE TO {username} CONTAINER=ALL")
            cursor.execute(f"GRANT CREATE SESSION TO {username} CONTAINER=ALL")
            
            conn.commit()
            print(f"   ✅ Created {username} with DBA grants (CDB common user)")
            return True
        except Exception as e:
            print(f"   ❌ Failed to create {username}: {e}")
            return False
    
    def create_user_pdb(self, conn, pdb_name: str):
        """Create AIAUTO user in specific PDB"""
        username = "AIAUTO"
        cursor = conn.cursor()
        
        try:
            # Switch to PDB
            cursor.execute(f"ALTER SESSION SET CONTAINER = {pdb_name}")
            
            if self.user_exists(conn, username):
                print(f"   ⏭️ User {username} already exists in {pdb_name}")
                return True
            
            # Create user in PDB
            cursor.execute(f"""
                CREATE USER {username} IDENTIFIED BY "{self.AI_USER_PASSWORD}"
                DEFAULT TABLESPACE USERS
                TEMPORARY TABLESPACE TEMP
            """)
            
            # Grant privileges
            cursor.execute(f"GRANT DBA TO {username}")
            cursor.execute(f"GRANT SELECT ANY DICTIONARY TO {username}")
            cursor.execute(f"GRANT SELECT_CATALOG_ROLE TO {username}")
            cursor.execute(f"GRANT CREATE SESSION TO {username}")
            
            conn.commit()
            print(f"   ✅ Created {username} in PDB {pdb_name} with DBA grants")
            return True
        except Exception as e:
            print(f"   ❌ Failed to create {username} in {pdb_name}: {e}")
            return False
    
    def provision(self) -> bool:
        """Main provisioning method"""
        try:
            print(f"🔌 Connecting to Oracle {self.host}:{self.port}/{self.service_name}...")
            conn = self.connect_as_sysdba()
            
            cursor = conn.cursor()
            cursor.execute("SELECT NAME FROM V$DATABASE")
            db_name = cursor.fetchone()[0]
            print(f"   Connected to {db_name}")
            
            is_cdb = self.is_cdb(conn)
            print(f"   CDB: {is_cdb}")
            
            if is_cdb:
                # Create common user in CDB
                self.create_user_cdb(conn)
                
                # Also create in each PDB
                cursor.execute("SELECT PDB_NAME FROM V$PDBS WHERE PDB_NAME != 'PDB$SEED'")
                pdbs = [row[0] for row in cursor.fetchall()]
                for pdb in pdbs:
                    self.create_user_pdb(conn, pdb)
            else:
                # Non-CDB: create regular user
                self.create_user_pdb(conn, None)
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Oracle provisioning failed: {e}")
            return False


class PostgresUserProvisioner:
    """Creates monitoring user on PostgreSQL databases"""
    
    AI_USER_PASSWORD = os.getenv("AIAUTO_PASSWORD", "root")
    
    def __init__(self, host: str, port: int, 
                 admin_user: str = "postgres", admin_password: str = "root"):
        self.host = host
        self.port = port
        self.admin_user = admin_user
        self.admin_password = admin_password
    
    def connect(self):
        """Connect to PostgreSQL as admin"""
        if not PSYCOPG2_AVAILABLE:
            raise Exception("psycopg2 not available")
        
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.admin_user,
            password=self.admin_password,
            database="postgres"
        )
    
    def user_exists(self, conn, username: str) -> bool:
        """Check if user exists"""
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_roles WHERE rolname = '{username}'")
        return cursor.fetchone() is not None
    
    def provision(self) -> bool:
        """Create aiauto user with superuser grants"""
        username = "aiauto"
        
        try:
            print(f"🔌 Connecting to PostgreSQL {self.host}:{self.port}...")
            conn = self.connect()
            conn.autocommit = True
            cursor = conn.cursor()
            
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0][:50]
            print(f"   Connected: {version}...")
            
            if self.user_exists(conn, username):
                print(f"   ⏭️ User {username} already exists")
                # Ensure grants are correct
                cursor.execute(f"ALTER USER {username} WITH SUPERUSER")
                cursor.execute(f"GRANT pg_read_all_data TO {username}")
                cursor.execute(f"GRANT pg_monitor TO {username}")
                print(f"   ✅ Verified {username} has correct grants")
            else:
                # Create user
                cursor.execute(f"""
                    CREATE USER {username} WITH 
                    PASSWORD '{self.AI_USER_PASSWORD}'
                    SUPERUSER
                    CREATEDB
                    CREATEROLE
                """)
                
                # Additional grants
                cursor.execute(f"GRANT pg_read_all_data TO {username}")
                cursor.execute(f"GRANT pg_monitor TO {username}")
                
                print(f"   ✅ Created {username} with SUPERUSER grants")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ PostgreSQL provisioning failed: {e}")
            return False


class UserProvisionerAgent:
    """
    Main agent that provisions monitoring users on all databases in inventory.
    Creates: C##AIAUTO (Oracle CDB), AIAUTO (Oracle PDB/non-CDB), aiauto (PostgreSQL)
    """
    
    def __init__(self):
        self.mongo = MongoProxy()
        # Default admin credentials
        self.oracle_sys_password = os.getenv("ORACLE_PASSWORD", "root")
        self.postgres_password = os.getenv("POSTGRES_PASSWORD", "root")
        print("✅ UserProvisionerAgent initialized")
    
    def get_inventory(self):
        """Get all databases from inventory"""
        try:
            dbs = self.mongo.execute_eval("db.inventory_databases.find({}).toArray()")
            return dbs or []
        except:
            return []
    
    def run_once(self):
        """Provision users on all databases"""
        print(f"\n{'='*60}")
        print(f"👤 UserProvisioner Agent - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        inventory = self.get_inventory()
        print(f"📋 Found {len(inventory)} databases in inventory")
        
        success_count = 0
        
        for db in inventory:
            identity = db.get("identity", {})
            connection = db.get("connection", {})
            
            engine = identity.get("engine", "").upper()
            name = identity.get("db_unique_name", "UNKNOWN")
            host = identity.get("host", "127.0.0.1")
            port = connection.get("port", 5432)
            
            print(f"\n🔧 {name} ({engine}) - {host}:{port}")
            
            if engine == "ORACLE":
                service_name = connection.get("service_name", "ORCL")
                provisioner = OracleUserProvisioner(
                    host=host,
                    port=port,
                    service_name=service_name,
                    sys_password=self.oracle_sys_password
                )
                if provisioner.provision():
                    success_count += 1
                    
            elif engine in ["POSTGRES", "POSTGRESQL"]:
                provisioner = PostgresUserProvisioner(
                    host=host,
                    port=port,
                    admin_password=self.postgres_password
                )
                if provisioner.provision():
                    success_count += 1
            else:
                print(f"   ⏭️ Skipping {engine} (no provisioner)")
        
        print(f"\n✅ Provisioning complete. {success_count}/{len(inventory)} databases.")


def main():
    parser = argparse.ArgumentParser(description="UserProvisioner - Creates AI monitoring accounts")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--oracle", type=str, help="Provision single Oracle: host:port/service")
    parser.add_argument("--postgres", type=str, help="Provision single PostgreSQL: host:port")
    args = parser.parse_args()
    
    if args.oracle:
        # Parse host:port/service
        parts = args.oracle.split("/")
        service = parts[1] if len(parts) > 1 else "ORCL"
        host_port = parts[0].split(":")
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 1521
        
        provisioner = OracleUserProvisioner(host, port, service)
        provisioner.provision()
    elif args.postgres:
        # Parse host:port
        parts = args.postgres.split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 5432
        
        provisioner = PostgresUserProvisioner(host, port)
        provisioner.provision()
    else:
        agent = UserProvisionerAgent()
        agent.run_once()


if __name__ == "__main__":
    main()
