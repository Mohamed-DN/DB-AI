"""Verify and fix SYSMAN user"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('127.0.0.1', port=2200, username='oracle', password='root')

# Check user in PDB
check_sql = """
set echo off
set feedback off
set heading off
ALTER SESSION SET CONTAINER=FREEPDB1;
SELECT 'SYSMAN EXISTS: ' || COUNT(*) FROM dba_users WHERE username='SYSMAN';
"""

cmd = f'echo "{check_sql}" | sqlplus -s / as sysdba'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
out = stdout.read().decode()
print(f"Check: {out}")

# If not exists, create
if 'SYSMAN EXISTS: 0' in out or 'no rows' in out.lower():
    print("Creating SYSMAN...")
    create_sql = """
    ALTER SESSION SET CONTAINER=FREEPDB1;
    CREATE USER sysman IDENTIFIED BY sysman123;
    GRANT DBA TO sysman;
    """
    cmd2 = f'echo "{create_sql}" | sqlplus -s / as sysdba'
    stdin, stdout, stderr = ssh.exec_command(cmd2, timeout=30)
    print(stdout.read().decode())

# Test connection via tnsping equivalent
test_sql = """
set feedback off
CONNECT sysman/sysman123@//localhost:1521/FREEPDB1
SELECT 'CONNECTED AS: ' || USER FROM DUAL;
EXIT;
"""
cmd3 = f'echo "{test_sql}" | sqlplus -s /nolog'
stdin, stdout, stderr = ssh.exec_command(cmd3, timeout=30)
print(f"Connection test: {stdout.read().decode()}")

ssh.close()
