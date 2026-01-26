"""
Start Oracle Listener on VMs via SSH
"""
import paramiko
import time

VMS = [
    {'name': 'VM1', 'host': '127.0.0.1', 'port': 2200},
    {'name': 'VM2', 'host': '127.0.0.1', 'port': 2201}
]

SSH_USER = 'oracle'
SSH_PASS = 'root'

def execute_ssh_command(ssh, command, timeout=10):
    """Execute command via SSH"""
    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return output, error

def start_listener(vm):
    """Connect and start Oracle listener"""
    print(f"\n📡 {vm['name']}: Checking Oracle listener...")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=vm['host'],
            port=vm['port'],
            username=SSH_USER,
            password=SSH_PASS,
            timeout=10
        )
        
        # Check listener status
        out, err = execute_ssh_command(ssh, "lsnrctl status")
        
        if 'no listener' in out.lower() or 'TNS-12541' in out or 'TNS-01106' in out:
            print(f"  ⚠️  Listener not running, starting...")
            out, err = execute_ssh_command(ssh, "lsnrctl start", timeout=30)
            
            if 'The command completed successfully' in out or 'started' in out.lower():
                print(f"  ✅ Listener started successfully")
                # Wait a moment for listener to initialize
                time.sleep(2)
                # Show status
                out, err = execute_ssh_command(ssh, "lsnrctl status")
                print("  📊 Listener Status:")
                for line in out.split('\n'):
                    if 'Service' in line or 'Instance' in line or 'STATUS' in line:
                        print(f"    {line.strip()}")
            else:
                print(f"  ❌ Failed to start listener")
                print(f"  Error: {err}")
        else:
            print(f"  ✅ Listener already running")
            for line in out.split('\n'):
                if 'Service' in line or 'Instance' in line:
                    print(f"    {line.strip()}")
        
        ssh.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("🚀 Starting Oracle Listeners on VMs...")
    print("=" * 60)
    
    for vm in VMS:
        start_listener(vm)
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("✅ Done! Test Oracle connection now:")
    print("   python ops/scripts/oem_scraper.py --discover-from-mongo --once")

if __name__ == "__main__":
    main()
