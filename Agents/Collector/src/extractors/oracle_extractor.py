"""
Oracle Database Extractor
Extracts configuration, storage, and performance data from Oracle databases.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import re


@dataclass
class OracleExtractor:
    """Extract Oracle database information via SQL"""

    # SQL to get basic database info
    SQL_DB_INFO = """
    SELECT 
        d.name as db_name,
        d.db_unique_name,
        d.database_role,
        d.open_mode,
        i.version,
        i.instance_name,
        i.host_name,
        i.status as instance_status
    FROM v$database d, v$instance i
    """

    # SQL to get Oracle Home
    SQL_ORACLE_HOME = """
    SELECT SYS_CONTEXT('USERENV', 'ORACLE_HOME') as oracle_home FROM DUAL
    """

    # SQL to get installed patches
    SQL_PATCHES = """
    SELECT patch_id, description, action_time
    FROM dba_registry_sqlpatch
    WHERE status = 'SUCCESS'
    ORDER BY action_time DESC
    """

    # SQL to get ASM diskgroups
    SQL_ASM_DISKGROUPS = """
    SELECT 
        name,
        total_mb / 1024 as total_gb,
        free_mb / 1024 as free_gb,
        ROUND((1 - free_mb/total_mb) * 100, 2) as used_pct,
        state
    FROM v$asm_diskgroup
    """

    # SQL to get tablespaces
    SQL_TABLESPACES = """
    SELECT 
        tablespace_name,
        ROUND(used_space * 8192 / 1024 / 1024 / 1024, 2) as used_gb,
        ROUND(tablespace_size * 8192 / 1024 / 1024 / 1024, 2) as max_gb,
        ROUND(used_percent, 2) as used_pct,
        CASE WHEN max_size = 0 THEN 'NO' ELSE 'YES' END as autoextensible
    FROM dba_tablespace_usage_metrics
    """

    # SQL to get RAC nodes
    SQL_RAC_NODES = """
    SELECT 
        inst_id,
        instance_name,
        host_name,
        status,
        database_status
    FROM gv$instance
    """

    # SQL to get Data Guard status
    SQL_DATAGUARD = """
    SELECT 
        dest_id,
        dest_name,
        status,
        db_unique_name,
        synchronization_status,
        gap_status
    FROM v$archive_dest_status
    WHERE dest_id > 1 AND status != 'INACTIVE'
    """

    # SQL to get licensing info
    SQL_LICENSE_OPTIONS = """
    SELECT 
        name,
        detected_usages,
        currently_used
    FROM dba_feature_usage_statistics
    WHERE currently_used = 'TRUE'
    AND name IN ('Real Application Clusters', 'Partitioning', 
                 'Diagnostics Pack', 'Tuning Pack', 'Advanced Compression')
    """

    # SQL to get PDBs (for CDB)
    SQL_PDBS = """
    SELECT 
        pdb_name,
        status,
        open_mode
    FROM dba_pdbs
    WHERE pdb_name != 'PDB$SEED'
    """

    # SQL to get SGA/PGA info
    SQL_MEMORY = """
    SELECT 
        name,
        ROUND(value / 1024 / 1024 / 1024, 2) as value_gb
    FROM v$sga
    UNION ALL
    SELECT 
        'PGA' as name,
        ROUND(value / 1024 / 1024 / 1024, 2) as value_gb
    FROM v$pgastat
    WHERE name = 'total PGA allocated'
    """

    @staticmethod
    def parse_sqlplus_output(output: str) -> List[Dict]:
        """Parse SQLPlus output into list of dicts"""
        lines = output.strip().split('\n')
        if len(lines) < 3:
            return []
        
        # Find header line (contains column names)
        headers = []
        data_start = 0
        for i, line in enumerate(lines):
            if '---' in line:
                headers = lines[i-1].split()
                data_start = i + 1
                break
        
        if not headers:
            return []
        
        results = []
        for line in lines[data_start:]:
            if line.strip() and not line.startswith('SQL>'):
                values = line.split()
                if len(values) >= len(headers):
                    row = dict(zip(headers, values[:len(headers)]))
                    results.append(row)
        
        return results

    @staticmethod
    def generate_sqlplus_command(sql: str) -> str:
        """Generate SQLPlus command string"""
        return f'''sqlplus -s / as sysdba <<EOF
SET PAGESIZE 1000
SET LINESIZE 200
SET HEADING ON
SET FEEDBACK OFF
{sql}
EXIT;
EOF'''


class OracleDataCollector:
    """Collects and normalizes Oracle data"""

    def __init__(self, ssh_executor):
        """
        Args:
            ssh_executor: Function that executes commands on remote host
                         Returns (stdout, stderr, exit_code)
        """
        self.executor = ssh_executor
        self.extractor = OracleExtractor()

    def collect_all(self) -> Dict:
        """Collect all Oracle data"""
        data = {}
        
        # Basic info
        data["db_info"] = self._run_query(OracleExtractor.SQL_DB_INFO)
        data["oracle_home"] = self._run_query(OracleExtractor.SQL_ORACLE_HOME)
        data["patches"] = self._run_query(OracleExtractor.SQL_PATCHES)
        
        # Storage
        data["diskgroups"] = self._run_query(OracleExtractor.SQL_ASM_DISKGROUPS)
        data["tablespaces"] = self._run_query(OracleExtractor.SQL_TABLESPACES)
        
        # Architecture
        data["rac_nodes"] = self._run_query(OracleExtractor.SQL_RAC_NODES)
        data["dataguard"] = self._run_query(OracleExtractor.SQL_DATAGUARD)
        data["pdbs"] = self._run_query(OracleExtractor.SQL_PDBS)
        
        # Licensing
        data["license_options"] = self._run_query(OracleExtractor.SQL_LICENSE_OPTIONS)
        
        # Memory
        data["memory"] = self._run_query(OracleExtractor.SQL_MEMORY)
        
        return data

    def _run_query(self, sql: str) -> List[Dict]:
        """Run SQL query and parse results"""
        cmd = OracleExtractor.generate_sqlplus_command(sql)
        stdout, stderr, exit_code = self.executor(cmd)
        
        if exit_code != 0:
            return []
        
        return OracleExtractor.parse_sqlplus_output(stdout)
