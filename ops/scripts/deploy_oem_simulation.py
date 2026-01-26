"""
Deploy OEM Simulation via SFTP + SSH
"""
import paramiko
import os

VM = {'host': '127.0.0.1', 'port': 2200}
SQL_FILE = 'ops/sql/setup_oem_simulation.sql'
REMOTE_PATH = '/tmp/setup_oem.sql'

print("🚀 Deploying OEM Repository Simulation...")

# Read local SQL file
with open(SQL_FILE, 'r') as f:
    sql_content = f.read()

# Connect SSH
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VM['host'], port=VM['port'], username='oracle', password='root', timeout=15)
print("✅ SSH connected")

# Upload via SFTP
sftp = ssh.open_sftp()
with sftp.open(REMOTE_PATH, 'w') as remote_file:
    remote_file.write(sql_content)
sftp.close()
print(f"✅ SQL file uploaded to {REMOTE_PATH}")

# Execute SQL
print("🔧 Executing SQL script...")
cmd = f"sqlplus / as sysdba @{REMOTE_PATH}"
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)

output = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')

# Check results
if 'User created' in output or 'created' in output.lower():
    print("✅ SYSMAN user created!")
    
if 'PL/SQL procedure successfully completed' in output:
    print("✅ Sample data inserted!")

# Show counts
for line in output.split('\n'):
    if 'Targets:' in line or 'Hosts:' in line or 'Metrics:' in line:
        print(f"  📊 {line.strip()}")

if 'ORA-' in output:
    print("⚠️ Some errors occurred:")
    for line in output.split('\n'):
        if 'ORA-' in line:
            print(f"  {line[:80]}")

# Cleanup
ssh.exec_command(f"rm {REMOTE_PATH}")
ssh.close()

print("\n✅ OEM Repository Simulation deployed!")
print("\n🚀 Test command:")
print("python ops/scripts/oem_repository_collector.py --oem-host 127.0.0.1 --oem-port 2521 --oem-service FREEPDB1 --oem-user sysman --oem-pass sysman123 --once")
