"""Direct SYSMAN user fix"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('127.0.0.1', port=2200, username='oracle', password='root')
print("SSH OK")

# First check and fix SYSMAN
sql = """
ALTER SESSION SET CONTAINER=FREEPDB1;
SELECT username FROM dba_users WHERE username='SYSMAN';
"""
cmd = f"sqlplus -s / as sysdba <<'EOF'\n{sql}\nEOF"
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
out = stdout.read().decode()
print(f"Check SYSMAN: {out}")

# Create/recreate
sql2 = """
ALTER SESSION SET CONTAINER=FREEPDB1;
DROP USER sysman CASCADE;
CREATE USER sysman IDENTIFIED BY sysman123;
GRANT DBA TO sysman;
ALTER USER sysman QUOTA UNLIMITED ON users;
SELECT username FROM dba_users WHERE username='SYSMAN';
EXIT;
"""
cmd2 = f"sqlplus -s / as sysdba <<'EOF'\n{sql2}\nEOF"
stdin, stdout, stderr = ssh.exec_command(cmd2, timeout=30)
out2 = stdout.read().decode()
print(f"Recreate: {out2}")
ssh.close()
print("Done")
