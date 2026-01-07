"""
Remote Oracle Database Extractor
Extracts configuration, storage, and performance data from Remote Oracle databases (e.g. VirtualBox)
Uses python-oracledb instead of local SQLPlus
"""
import oracledb
import datetime
from typing import Dict, List, Optional
from .oracle_extractor import OracleExtractor

class RemoteOracleExtractor:
    """Collects Oracle data via direct TCP connection"""

    def __init__(self, host: str, port: int, service_name: str, user: str, password: str):
        self.dsn = f"{host}:{port}/{service_name}"
        self.user = user
        self.password = password
        self.extractor = OracleExtractor()

    def collect_all(self) -> Dict:
        """Collect all Oracle data"""
        data = {}
        
        try:
            # Connect
            params = {
                "user": self.user,
                "password": self.password,
                "dsn": self.dsn
            }
            if self.user.lower() == 'sys':
                params["mode"] = oracledb.AUTH_MODE_SYSDBA

            with oracledb.connect(**params) as connection:
                with connection.cursor() as cursor:
                    
                    # Helper to run query
                    def run(sql):
                        try:
                            cursor.execute(sql)
                            columns = [col[0] for col in cursor.description]
                            cursor.rowfactory = lambda *args: dict(zip(columns, args))
                            return cursor.fetchall()
                        except Exception as e:
                            print(f"Query Error ({sql[:20]}...): {e}")
                            return []

                    # Basic info
                    data["db_info"] = run(OracleExtractor.SQL_DB_INFO)
                    
                    # Debug Container
                    curr_con = run(OracleExtractor.SQL_CURRENT_CONTAINER)
                    print(f"   ℹ️  Connected to Container: {curr_con[0]['CONTAINER'] if curr_con else 'UNKNOWN'}")

                    data["oracle_home"] = run(OracleExtractor.SQL_ORACLE_HOME)
                    data["patches"] = run(OracleExtractor.SQL_PATCHES)
                    
                    # Storage
                    data["diskgroups"] = run(OracleExtractor.SQL_ASM_DISKGROUPS)
                    data["tablespaces"] = run(OracleExtractor.SQL_TABLESPACES)
                    
                    # Architecture
                    data["rac_nodes"] = run(OracleExtractor.SQL_RAC_NODES)
                    data["dataguard"] = run(OracleExtractor.SQL_DATAGUARD)
                    data["pdbs"] = run(OracleExtractor.SQL_PDBS)
                    print(f"   ℹ️  PDBs Collected: {len(data['pdbs'])}")
                    if len(data['pdbs']) == 0:
                        print("   ⚠️  WARNING: No PDBs returned from dba_pdbs")
                    
                    # Licensing
                    data["license_options"] = run(OracleExtractor.SQL_LICENSE_OPTIONS)
                    
                    # Memory
                    data["memory"] = run(OracleExtractor.SQL_MEMORY)

        except Exception as e:
            print(f"Connection Failed to {self.dsn}: {e}")
            return {}
        
        return data
