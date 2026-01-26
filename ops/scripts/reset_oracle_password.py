"""
Reset Oracle SYSTEM password via SSH
"""
import paramiko
import time

VM = {'name': 'VM1', 'host': '127.0.0.1', 'port': 2200}
SSH_USER = 'oracle'
SSH_PASS = 'root'

print("🔑 Resetting Oracle SYSTEM password...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=VM['host'],
        port=VM['port'],
        username=SSH_USER,
        password=SSH_PASS,
        timeout=15
    )
    
    print("  ✅ SSH connected")
    
    # Reset password using SQL command
    sql_cmd = """sqlplus -s / as sysdba <<EOF
ALTER USER system IDENTIFIED BY root;
ALTER SESSION SET CONTAINER=FREEPDB1;
ALTER USER system IDENTIFIED BY root;
EXIT;
EOF"""
    
    print("  🔧 Executing password reset...")
    stdin, stdout, stderr = ssh.exec_command(sql_cmd, timeout=30)
    
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if 'altered' in output.lower() or 'User altered' in output:
        print("  ✅ Password reset successful!")
        print("  📊 Output:", output[:200])
    else:
        print("  ⚠️  Unexpected output:")
        print("  ", output[:300])
        if error:
            print("  Error:", error[:200])
    
    ssh.close()
    print("\n✅ Done! Test connection now:")
    print("   python ops/scripts/oem_scraper.py --oracle-host 127.0.0.1 --oracle-port 2521 --oracle-service FREEPDB1 --oracle-user system --oracle-pass root --once")
    
except Exception as e:
    print(f"  ❌ Error: {e}")
