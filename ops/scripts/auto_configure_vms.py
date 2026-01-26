"""
Auto-configure Oracle VMs via SSH
=================================
Connects to VMs, discovers Oracle SID, updates configuration
"""
import paramiko
import time
import sys
import re

VMS = [
    {'name': 'VM1', 'host': '127.0.0.1', 'port': 2200, 'oracle_port': 2521},
    {'name': 'VM2', 'host': '127.0.0.1', 'port': 2201, 'oracle_port': 2522}
]

SSH_USER = 'oracle'
SSH_PASS = 'root'

def execute_ssh_command(ssh, command, timeout=10):
    """Execute command via SSH and return output"""
    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return output, error

def discover_oracle_config(vm):
    """Connect to VM and discover Oracle configuration"""
    print(f"\n📡 Connecting to {vm['name']} via SSH...")
    
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
        
        print(f"  ✅ SSH connected")
        
        # 1. Check listener status
        print(f"  🔍 Checking Oracle listener...")
        out, err = execute_ssh_command(ssh, "lsnrctl status 2>/dev/null || echo 'NO_LISTENER'")
        
        sid = None
        service_name = None
        
        if 'NO_LISTENER' in out:
            print(f"  ⚠️  Listener not running or not found")
            # Try to find Oracle via pmon process
            out, err = execute_ssh_command(ssh, "ps -ef | grep pmon | grep -v grep || echo 'NO_PMON'")
            if 'ora_pmon_' in out:
                match = re.search(r'ora_pmon_(\w+)', out)
                if match:
                    sid = match.group(1)
                    print(f"  ✅ Found Oracle process: ora_pmon_{sid}")
        else:
            # Parse listener output
            # Look for service names like: Service "FREE" has 1 instance(s)
            services = re.findall(r'Service\s+"([^"]+)"', out)
            if services:
                service_name = services[0]
                print(f"  ✅ Found service: {service_name}")
            
            # Also look for instance names
            instances = re.findall(r'Instance\s+"([^"]+)"', out)
            if instances:
                sid = instances[0]
                print(f"  ✅ Found instance: {sid}")
        
        # 2. Check /etc/oratab
        print(f"  🔍 Checking /etc/oratab...")
        out, err = execute_ssh_command(ssh, "cat /etc/oratab 2>/dev/null | grep -v '^#' | grep -v '^$' || echo 'NO_ORATAB'")
        
        if 'NO_ORATAB' not in out:
            for line in out.strip().split('\n'):
                if ':' in line and not line.startswith('#'):
                    parts = line.split(':')
                    if parts[0]:
                        found_sid = parts[0]
                        print(f"  📋 /etc/oratab entry: {found_sid}")
                        if not sid:
                            sid = found_sid
        
        ssh.close()
        
        result = {
            'name': vm['name'],
            'host': vm['host'],
            'oracle_port': vm['oracle_port'],
            'sid': sid or service_name,
            'service_name': service_name,
            'ssh_success': True
        }
        
        if result['sid']:
            print(f"  ✅ Discovered SID/Service: {result['sid']}")
        else:
            print(f"  ❌ Could not determine SID")
        
        return result
        
    except Exception as e:
        print(f"  ❌ SSH error: {e}")
        return {
            'name': vm['name'],
            'ssh_success': False,
            'error': str(e)
        }

def main():
    print("🚀 Auto-configuring Oracle VMs...")
    print("=" * 60)
    
    discovered = []
    
    for vm in VMS:
        config = discover_oracle_config(vm)
        discovered.append(config)
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("📊 Discovery Results:")
    
    for config in discovered:
        print(f"\n{config['name']}:")
        if config.get('ssh_success'):
            if config.get('sid'):
                print(f"  ✅ SID: {config['sid']}")
                print(f"  Host: {config['host']}")
                print(f"  Port: {config['oracle_port']}")
            else:
                print(f"  ⚠️  Oracle found but SID unclear")
        else:
            print(f"  ❌ SSH failed: {config.get('error', 'Unknown')}")
    
    # Save results
    successful = [c for c in discovered if c.get('ssh_success') and c.get('sid')]
    
    if successful:
        print(f"\n✅ Found {len(successful)} working Oracle configuration(s)")
        
        # Generate update command
        print("\n🔧 To update MongoDB with these SIDs:")
        for config in successful:
            print(f"\n# {config['name']}:")
            print(f"db.inventory_databases.updateOne(")
            print(f"  {{_id: 'ORACLE_{config['name'].upper()}_DEV'}},")
            print(f"  {{$set: {{'identity.sid': '{config['sid']}'}} }}")
            print(f")")
        
        return 0
    else:
        print("\n❌ No Oracle configurations auto-discovered")
        print("   Manual intervention required")
        return 1

if __name__ == "__main__":
    sys.exit(main())
