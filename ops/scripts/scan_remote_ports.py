import paramiko

def scan():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect('127.0.0.1', 2200, username='oracle', password='root')
        
        print("\n--- LISTENING PORTS ---")
        # Try multiple commands to find one that works
        stdin, stdout, stderr = client.exec_command("netstat -tln | awk '{print $4}' | grep ':'")
        print(stdout.read().decode())
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    scan()
