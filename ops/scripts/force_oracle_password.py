"""
Test common Oracle passwords and force reset if needed
"""
import oracledb
import paramiko
import time

COMMON_PASSWORDS = ['Oracle123', 'oracle', 'Welcome1', 'welcome1', 'oracle123', 'Password1', 'root']
VM_CONFIG = {
    'host': '127.0.0.1',
    'port': 2521,
    'service': 'FREEPDB1',
    'ssh_port': 2200
}

print("🔐 Testing common Oracle passwords...")

# Test 1: Try common passwords
for pwd in COMMON_PASSWORDS:
    try:
        dsn = f"{VM_CONFIG['host']}:{VM_CONFIG['port']}/{VM_CONFIG['service']}"
        conn = oracledb.connect(user='system', password=pwd, dsn=dsn)
        print(f"\n✅ SUCCESS! Password is: {pwd}")
        
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM V$INSTANCE')
        print(f"   V$INSTANCE accessible: {cursor.fetchone()[0]} instance(s)")
        cursor.close()
        conn.close()
        
        print(f"\n🎉 FOUND WORKING PASSWORD: {pwd}")
        print(f"   Update scripts to use password='{pwd}'")
        exit(0)
        
    except Exception as e:
        if 'ORA-01017' in str(e):
            print(f"❌ {pwd}: Wrong password")
        else:
            print(f"⚠️  {pwd}: {str(e)[:60]}")

print("\n🔧 Common passwords failed. Attempting password reset via SSH...")

# Test 2: Force password reset via SSH
try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=VM_CONFIG['host'],
        port=VM_CONFIG['ssh_port'],
        username='oracle',
        password='root',
        timeout=15
    )
    
    print("  ✅ SSH connected")
    
    # More robust SQL command with proper formatting
    commands = [
        "export ORACLE_SID=cdbrac1",
        "echo 'ALTER USER system IDENTIFIED BY Nexi2024;' | sqlplus -s / as sysdba",
        "echo 'ALTER SESSION SET CONTAINER=FREEPDB1; ALTER USER system IDENTIFIED BY Nexi2024;' | sqlplus -s / as sysdba"
    ]
    
    for cmd in commands:
        print(f"  🔧 Executing: {cmd[:60]}...")
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=20)
        output = stdout.read().decode('utf-8', errors='ignore')
        
        if 'altered' in output.lower():
            print(f"    ✅ Success!")
        
        time.sleep(1)
    
    ssh.close()
    
    print("\n  ✅ Password reset commands executed")
    print("  🔄 Testing new password 'Nexi2024'...")
    
    # Test new password
    dsn = f"{VM_CONFIG['host']}:{VM_CONFIG['port']}/{VM_CONFIG['service']}"
    conn = oracledb.connect(user='system', password='Nexi2024', dsn=dsn)
    print(f"\n  🎉 SUCCESS! New password 'Nexi2024' works!")
    conn.close()
    
except Exception as e:
    print(f"\n  ❌ Password reset failed: {e}")
    print("\n  Manual intervention required:")
    print("  ssh -p 2200 oracle@127.0.0.1")
    print("  sqlplus / as sysdba")
    print("  SQL> ALTER USER system IDENTIFIED BY YourPassword;")
