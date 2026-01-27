import paramiko

def scan():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print("Connecting to NODE 1 (2200)...")
        client.connect('127.0.0.1', 2200, username='oracle', password='root')
        
        print("\n--- SEARCHING portlist.ini ---")
        # Search in typical locations to save time, then broad search
        cmd = "cat /u01/app/oracle/product/*/dbhome_1/install/portlist.ini 2>/dev/null || find /u01 -name portlist.ini -maxdepth 8 -exec cat {} +"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        print("\n--- CHECKING emoms.properties ---")
        cmd = "find /u01 -name emoms.properties -maxdepth 8 -exec grep 'oracle.sysman.eml.mntr.emdRepPort' {} +"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    scan()
