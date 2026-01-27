import paramiko

def scan():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print("Connecting to NODE 1...")
        client.connect('127.0.0.1', 2200, username='oracle', password='root')
        
        # Try a very broad search and print results clearly
        print("\n--- FINDING portlist.ini ---")
        stdin, stdout, stderr = client.exec_command("find /u01 -name portlist.ini 2>/dev/null")
        files = stdout.read().decode().splitlines()
        
        if not files:
            print("No portlist.ini found.")
        
        for f in files:
            print(f"Reading {f}:")
            stdin, stdout, stderr = client.exec_command(f"cat {f}")
            print(stdout.read().decode())

        # Check for emoms.properties
        print("\n--- FINDING emoms.properties ---")
        stdin, stdout, stderr = client.exec_command("find /u01 -name emoms.properties 2>/dev/null")
        props = stdout.read().decode().splitlines()
        for p in props:
            print(f"Reading {p} (grep Port):")
            stdin, stdout, stderr = client.exec_command(f"grep Port {p}")
            print(stdout.read().decode())
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    scan()
