import json
import subprocess
import logging

class OracleExtractor:
    def __init__(self):
        pass

    def _exec_sqlplus_json(self, container: str, sql: str):
        """
        Execute a SQL query inside the container via sqlplus.
        Since sqlplus doesn't have --json until very new versions, we use a trick:
        Set markup CSV on, then use python to parse CSV to Dict.
        """
        try:
            # Construct a full SQL script to be piped
            full_script = f"""
            SET MARKUP CSV ON QUOTE OFF
            SET FEEDBACK OFF
            SET PAGESIZE 50000
            SET HEADING ON
            {sql}
            EXIT;
            """
            
            # Using 'sh -c' to handle piping properly inside docker exec if needed, 
            # but usually passing input via stdin is cleaner.
            # We assume user is 'system' or 'sys as sysdba' via a wrapper or direct env var.
            # For this container: user nexi_app or system? 
            # We'll use 'sqlplus -S / as sysdba' assuming OS auth is set up in these containers (gvenzl/oracle-free usually allows it for oracle user)
            
            cmd = [
                "docker", "exec", "-i", container, 
                "sqlplus", "-S", "/", "as", "sysdba"
            ]
            
            # Pass SQL via stdin
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(input=full_script)
            
            if stderr and "ORA-" in stderr:
                print(f"⚠️ SQLPlus Error: {stderr}")
                return []
                
            # Parse CSV output
            results = []
            lines = stdout.strip().split('\n')
            if len(lines) < 2:
                return []
                
            headers = [h.strip().upper() for h in lines[0].split(',')]
            for line in lines[1:]:
                if not line.strip(): continue
                values = line.split(',')
                if len(values) == len(headers):
                    row = {}
                    for i, h in enumerate(headers):
                        val = values[i].strip()
                        # basic type inference
                        if val.isdigit():
                            val = int(val)
                        row[h] = val
                    results.append(row)
            
            return results

        except Exception as e:
            # print(f"⚠️ Oracle Query Error on {container}: {e}") # Verbose
            return []


    def _exec_os_command(self, container: str, command: list):
        """Execute an arbitrary OS command inside the container"""
        try:
            # We assume user is 'oracle' or 'grid' for these commands, or root with su -
            # For this lab: 'oracle' user via su
            # cmd_str = " ".join(command)
            # cmd = ["docker", "exec", container, "su", "-", "oracle", "-c", cmd_str]
            
            # Simple direct exec for the lab (often running as root or oracle default)
            cmd = ["docker", "exec", container] + command
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return ""
        except Exception:
            return ""

    def extract(self, container: str, db_unique_name: str):
        """Deep extract for Oracle"""
        print(f"🔮 Oracle Deep Extraction for {container}...")
        
        # 1. Cluster Identity & Version
        ident_q = "SELECT db_unique_name, dbid, platform_name, version, database_role, open_mode FROM v$database, v$instance"
        ident_res = self._exec_sqlplus_json(container, ident_q)
        ident_data = ident_res[0] if ident_res else {}

        # 2. Instances
        inst_q = "SELECT inst_id, instance_name, host_name, status, database_status, logins FROM gv$instance"
        instances = self._exec_sqlplus_json(container, inst_q)

        # 3. ASM Disk Groups 
        asm_q = "SELECT group_number, name, state, type, total_mb, free_mb, offline_disks FROM v$asm_diskgroup"
        asm_res = self._exec_sqlplus_json(container, asm_q)

        # 4. Data Guard
        dg_q = "SELECT name, value, unit, time_computed FROM v$dataguard_stats WHERE name IN ('transport lag', 'apply lag')"
        dg_res = self._exec_sqlplus_json(container, dg_q)
        
        # 5. RMAN Last Backup
        rman_q = "SELECT status, start_time, end_time, input_bytes, output_bytes FROM v$rman_status WHERE operation = 'BACKUP' AND row_type = 'SESSION' ORDER BY start_time DESC FETCH FIRST 1 ROWS ONLY"
        rman_res = self._exec_sqlplus_json(container, rman_q)

        # 6. GoldenGate (Simple Check via Processes)
        gg_q = "SELECT count(*) as gg_sessions FROM v$session WHERE program LIKE '%extract%' OR program LIKE '%replicat%'"
        gg_res = self._exec_sqlplus_json(container, gg_q)
        gg_active = False
        if gg_res and gg_res[0].get('GG_SESSIONS', 0) > 0:
             gg_active = True

        # 7. OS/CLI Status (New)
        # Try to gather High Availability status from OS commands
        # Note: In the demo container (gvenzl/oracle-free), these might not exist or return errors, 
        # but this logic handles the Enterprise requirement.
        
        crs_out = self._exec_os_command(container, ["crsctl", "check", "has"])
        srv_out = self._exec_os_command(container, ["srvctl", "status", "database", "-d", db_unique_name, "-v"])
        
        # Determine Role from SRVCTL if available, else fall back to SQL
        cli_role = "UNKNOWN"
        if "PRIMARY" in srv_out.upper(): cli_role = "PRIMARY"
        elif "STANDBY" in srv_out.upper(): cli_role = "PHYSICAL STANDBY"
        
        # DGMGRL needs sys password. Hardcoded for lab or env var?
        # dgmgrl sys/nexi2024@//localhost:1521/CONF "show configuration verbose"
        # Skipping for safety in auto-mode unless strictly required, relying on SQL views for DG details.
             
        # Build Deep JSON
        deep_metadata = {
            "metadata_version": "2.1-deep",
            "extraction_timestamp": "NOW",
            "cluster_identity": {
                "db_unique_name": ident_data.get('DB_UNIQUE_NAME', db_unique_name),
                "dbid": ident_data.get('DBID'),
                "platform_name": ident_data.get('PLATFORM_NAME'),
                "version_full": ident_data.get('VERSION'),
                "database_role": ident_data.get('DATABASE_ROLE'),
                "open_mode": ident_data.get('OPEN_MODE')
            },
            "instances": instances,
            "ha_dr": {
                "architecture": "SINGLE" if len(instances) < 2 else "RAC",
                "nodes": len(instances),
                "cli_status": {
                    "crsctl_output": crs_out,
                    "srvctl_status": srv_out,
                    "derived_role": cli_role
                },
                "dataguard": {
                    "status": ident_data.get('DATABASE_ROLE', 'PRIMARY'),
                    "lag_metrics": dg_res
                },
                "goldengate": {
                    "present": gg_active,
                    "status": "RUNNING" if gg_active else "UNKNOWN"
                }
            },
            "backup_health": {
                "last_full_backup": rman_res[0] if rman_res else {"status": "UNKNOWN"}
            },
            "storage_deep_dive": {
                "asm_disk_groups": asm_res
            }
        }
        
        return deep_metadata
