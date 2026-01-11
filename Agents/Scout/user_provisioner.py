"""
User Provisioner - Automatically creates AIAUTO management user on discovered databases
"""
import subprocess
import os


class UserProvisioner:
    """Creates and manages AIAUTO user across different database engines"""
    
    # User creation SQL templates
    ORACLE_CDB_SQL = """
CREATE USER C##AIAUTO IDENTIFIED BY root CONTAINER=ALL;
GRANT DBA TO C##AIAUTO CONTAINER=ALL;
GRANT SELECT ANY DICTIONARY TO C##AIAUTO CONTAINER=ALL;
GRANT UNLIMITED TABLESPACE TO C##AIAUTO CONTAINER=ALL;
ALTER USER C##AIAUTO DEFAULT TABLESPACE USERS QUOTA UNLIMITED ON USERS CONTAINER=ALL;
"""

    ORACLE_PDB_SQL = """
CREATE USER AIAUTO IDENTIFIED BY root;
GRANT DBA TO AIAUTO;
GRANT SELECT ANY DICTIONARY TO AIAUTO;
GRANT UNLIMITED TABLESPACE TO AIAUTO;
"""

    POSTGRES_SQL = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'aiauto') THEN
        CREATE USER aiauto WITH PASSWORD 'root' SUPERUSER CREATEDB CREATEROLE LOGIN;
        RAISE NOTICE 'User aiauto created successfully';
    ELSE
        RAISE NOTICE 'User aiauto already exists';
    END IF;
END
$$;
"""

    MYSQL_SQL = """
CREATE USER IF NOT EXISTS 'aiauto'@'%' IDENTIFIED BY 'root';
GRANT ALL PRIVILEGES ON *.* TO 'aiauto'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
"""

    MONGO_JS = """
if (!db.getUser('aiauto')) {
    db.createUser({
        user: 'aiauto',
        pwd: 'root',
        roles: [{ role: 'root', db: 'admin' }]
    });
    print('User aiauto created');
} else {
    print('User aiauto already exists');
}
"""

    def __init__(self, mongo_proxy=None):
        self.mongo = mongo_proxy
        
    def check_user_exists(self, container: str, engine: str) -> bool:
        """Check if AIAUTO user already exists in the database"""
        try:
            if engine == 'POSTGRES':
                cmd = f"docker exec {container} psql -U postgres -tAc \"SELECT 1 FROM pg_user WHERE usename='aiauto'\""
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                return '1' in result.stdout
                
            elif engine == 'ORACLE':
                # Check for C##AIAUTO (CDB user)
                cmd = f"docker exec {container} sqlplus -s / as sysdba <<< \"SELECT 1 FROM dba_users WHERE username='C##AIAUTO';\""
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                return '1' in result.stdout
                
            elif engine == 'MYSQL':
                cmd = f"docker exec {container} mysql -u root -ppassword -e \"SELECT 1 FROM mysql.user WHERE user='aiauto'\" 2>/dev/null"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                return '1' in result.stdout
                
            elif engine == 'MONGODB':
                cmd = f"docker exec {container} mongosh admin --quiet --eval \"db.getUser('aiauto') ? 1 : 0\""
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                return '1' in result.stdout
                
        except Exception as e:
            print(f"⚠️ Error checking user existence: {e}")
        return False
        
    def create_user(self, container: str, engine: str, is_cdb: bool = True) -> tuple:
        """
        Create AIAUTO user with appropriate grants
        Returns: (success: bool, message: str)
        """
        try:
            print(f"👤 Provisioning AIAUTO user on {container} ({engine})...")
            
            if engine == 'POSTGRES':
                # Use DO block with IF NOT EXISTS for idempotency
                sql_escaped = self.POSTGRES_SQL.replace('\n', ' ').replace("'", "'\\''")
                cmd = f"docker exec {container} psql -U postgres -c \"{sql_escaped}\""
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    return True, "PostgreSQL: aiauto user created with SUPERUSER grants"
                else:
                    # If user already exists, that's fine
                    if 'already exists' in result.stderr.lower():
                        return True, "PostgreSQL: aiauto user already exists"
                    return False, f"PostgreSQL error: {result.stderr}"
                    
            elif engine == 'ORACLE':
                if is_cdb:
                    # Create common user C##AIAUTO
                    sql = self.ORACLE_CDB_SQL
                    user_check = "C##AIAUTO"
                else:
                    sql = self.ORACLE_PDB_SQL
                    user_check = "AIAUTO"
                
                # Check if user exists first
                check_cmd = f"docker exec {container} sqlplus -s / as sysdba <<EOF\nSET HEADING OFF FEEDBACK OFF\nSELECT COUNT(*) FROM dba_users WHERE username='{user_check}';\nEXIT;\nEOF"
                check_result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True, timeout=30)
                
                if '1' in check_result.stdout.strip():
                    return True, f"Oracle: {user_check} user already exists"
                
                # Create user
                create_cmd = f"docker exec {container} sqlplus -s / as sysdba <<EOF\n{sql}\nEXIT;\nEOF"
                result = subprocess.run(create_cmd, shell=True, capture_output=True, text=True, timeout=60)
                
                if 'ORA-' in result.stdout or 'ORA-' in result.stderr:
                    # Check if it's "user already exists" error
                    if 'ORA-01920' in result.stdout or 'ORA-01920' in result.stderr:
                        return True, f"Oracle: {user_check} user already exists"
                    return False, f"Oracle error: {result.stdout} {result.stderr}"
                    
                return True, f"Oracle: {user_check} user created with DBA grants"
                
            elif engine == 'MYSQL':
                sql_escaped = self.MYSQL_SQL.replace('\n', ' ')
                cmd = f"docker exec {container} mysql -u root -ppassword -e \"{sql_escaped}\" 2>/dev/null"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    return True, "MySQL: aiauto user created with ALL PRIVILEGES"
                return False, f"MySQL error: {result.stderr}"
                
            elif engine == 'MONGODB':
                cmd = f"docker exec {container} mongosh admin --quiet --eval \"{self.MONGO_JS}\""
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    return True, "MongoDB: aiauto user created with root role"
                return False, f"MongoDB error: {result.stderr}"
                
            else:
                return False, f"Unsupported engine: {engine}"
                
        except subprocess.TimeoutExpired:
            return False, f"Timeout while provisioning user on {container}"
        except Exception as e:
            return False, f"Exception: {str(e)}"
            
    def provision_database(self, db_info: dict) -> dict:
        """
        Main provisioning logic - check and create AIAUTO user
        Returns provisioning status dict
        """
        identity = db_info.get('identity', {})
        engine = identity.get('engine', 'UNKNOWN').upper()
        db_name = identity.get('db_name') or identity.get('db_unique_name', '').lower()
        
        if not db_name:
            return {"provisioned": False, "error": "No container name found"}
            
        # Check connection type - skip REMOTE databases (VirtualBox)
        conn_type = db_info.get('connection', {}).get('type', 'DOCKER')
        if conn_type == 'REMOTE':
            print(f"⏭️ Skipping REMOTE database {db_name} (use manual provisioning)")
            return {"provisioned": False, "skipped": True, "reason": "REMOTE connection type"}
            
        # Only provision supported engines
        if engine not in ['POSTGRES', 'ORACLE', 'MYSQL', 'MONGODB']:
            return {"provisioned": False, "error": f"Unsupported engine: {engine}"}
            
        # Check if already provisioned (via MongoDB flag)
        if self.mongo:
            existing = self.mongo.execute_eval(
                f"db.inventory_databases.findOne({{'identity.db_unique_name': '{identity.get('db_unique_name')}'}}, {{'provisioning': 1}})"
            )
            if existing and existing.get('provisioning', {}).get('aiauto_created'):
                print(f"✅ {db_name}: AIAUTO already provisioned (cached)")
                return {"provisioned": True, "cached": True}
        
        # Check if user exists directly
        if self.check_user_exists(db_name, engine):
            print(f"✅ {db_name}: AIAUTO user already exists")
            # Update MongoDB flag
            if self.mongo:
                self.mongo.execute_eval(f"""
                    db.inventory_databases.updateOne(
                        {{'identity.db_unique_name': '{identity.get('db_unique_name')}'}},
                        {{$set: {{'provisioning.aiauto_created': true, 'provisioning.aiauto_checked': new Date()}}}}
                    )
                """)
            return {"provisioned": True, "existing": True}
            
        # Create user
        is_cdb = engine == 'ORACLE'  # Assume Docker Oracle is CDB
        success, message = self.create_user(db_name, engine, is_cdb)
        
        print(f"{'✅' if success else '❌'} {db_name}: {message}")
        
        # Update MongoDB with provisioning status
        if self.mongo:
            status = "true" if success else "false"
            self.mongo.execute_eval(f"""
                db.inventory_databases.updateOne(
                    {{'identity.db_unique_name': '{identity.get('db_unique_name')}'}},
                    {{$set: {{
                        'provisioning.aiauto_created': {status},
                        'provisioning.aiauto_message': '{message.replace("'", "\\'")}',
                        'provisioning.aiauto_checked': new Date()
                    }}}}
                )
            """)
            
        return {"provisioned": success, "message": message}
