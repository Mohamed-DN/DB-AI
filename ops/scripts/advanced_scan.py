import paramiko
import re

def detailed_scan():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect('127.0.0.1', 2200, username='oracle', password='root')
        
        print("\n=== COMPLETE PORT ANALYSIS ===")
        # Get full process list with arguments to find OMS/EM
        stdin, stdout, stderr = client.exec_command("ps -ef | grep -E 'oms|emwd|java'")
        processes = stdout.read().decode()
        
        # Look for port numbers in process args (e.g. -Doracle.port=...)
        print("--- Process Arguments Hints ---")
        param_ports = re.findall(r'port[=\s]?(\d{4})', processes)
        print(f"Found potential ports in args: {list(set(param_ports))}")
        
        print("\n--- Listening Ports with Bind Address ---")
        stdin, stdout, stderr = client.exec_command("netstat -tlnp")
        netstat = stdout.read().decode()
        print(netstat)
        
        # Check /etc/hosts to see what hostname maps to
        print("\n--- /etc/hosts ---")
        stdin, stdout, stderr = client.exec_command("cat /etc/hosts")
        print(stdout.read().decode())
        
        # Check if emctl status works
        print("\n--- EMCTL Status ---")
        # Try generic paths
        cmds = [
            "/u01/app/oracle/middleware/oms/bin/emctl status oms -details",
            "/u01/app/oracle/product/19.0.0/dbhome_1/bin/emctl status dbconsole",
             "export ORACLE_HOME=/u01/app/oracle/product/19.0.0/dbhome_1; $ORACLE_HOME/bin/emctl status dbconsole",
             "ls -la /u01/app/oracle" # Discovery path
        ]
        
        for cmd in cmds:
            print(f"> Trying: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode()
            if out and "not found" not in out:
                print(out)
                break
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    detailed_scan()
