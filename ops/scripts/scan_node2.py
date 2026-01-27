import paramiko

def scan():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # Connect to NODE 2 (Port 2201)
        print("Connecting to NODE 2 (127.0.0.1:2201)...")
        client.connect('127.0.0.1', 2201, username='oracle', password='root')
        
        print("\n--- LISTENING PORTS (NODE 2) ---")
        stdin, stdout, stderr = client.exec_command("netstat -tln | awk '{print $4}' | grep ':'")
        print(stdout.read().decode())
        
        print("\n--- JAVA PROCESSES (NODE 2) ---")
        stdin, stdout, stderr = client.exec_command("ps -ef | grep java")
        print(stdout.read().decode())
            
    except Exception as e:
        print(f"Error connecting to Node 2: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    scan()
