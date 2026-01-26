"""
Grant Oracle monitoring permissions via SSH
"""
import paramiko

VM = {'host': '127.0.0.1', 'port': 2200}

grants = """
ALTER SESSION SET CONTAINER=FREEPDB1;
GRANT SELECT ON V_$INSTANCE TO system;
GRANT SELECT ON V_$DATABASE TO system;
GRANT SELECT ON V_$SESSION TO system;
GRANT SELECT ON V_$SYSSTAT TO system;
GRANT SELECT ON V_$SGASTAT TO system;
GRANT SELECT ON V_$PGASTAT TO system;
GRANT SELECT ON V_$SYSTEM_WAIT_CLASS TO system;
GRANT SELECT ON DBA_TABLESPACES TO system;
GRANT SELECT ON DBA_DATA_FILES TO system;
GRANT SELECT ON DBA_FREE_SPACE TO system;
GRANT SELECT_CATALOG_ROLE TO system;
EXIT;
"""

print("🔑 Granting Oracle monitoring permissions...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VM['host'], port=VM['port'], username='oracle', password='root', timeout=15)
    
    cmd = f"echo '{grants}' | sqlplus -s / as sysdba"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    
    output = stdout.read().decode('utf-8', errors='ignore')
    print(output if output else "  Grants executed")
    
    ssh.close()
    print("\n✅ Permissions granted!")
    
except Exception as e:
    print(f"❌ Error: {e}")
