import subprocess

def is_container_running(container_name):
    print(f"Checking {container_name}...")
    try:
        cmd = ["docker", "inspect", "-f", "{{.State.Running}}", container_name]
        output = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode('utf-8').strip()
        print(f"Output: '{output}'")
        return output == 'true'
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Stderr: {e.stderr.decode('utf-8')}")
        return False

print("Milano Dev Running?", is_container_running("m-dn-pg-milano-dev"))
