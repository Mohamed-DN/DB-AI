"""
Deploy Real CheckMK Agents
Downloads agents from local CheckMK server and installs them on DB containers.
Configures DB plugins (mk_postgres, mk_oracle).
"""
import subprocess
import os
import time

# Container Lists
PG_CONTAINERS = ["nexi-pg-milano-prod2", "nexi-pg-milano-dev2", "nexi-bratislava-prod", "nexi-pg-bratislava-prod2", "nexi-pg-bratislava-dev2"]
ORA_CONTAINERS = ["nexi-oracle-cairo-primary2", "nexi-oracle-cairo-replica2"]

def run_cmd(cmd, shell=False):
    # Helper to print and run
    # print(f"Exec: {cmd}") 
    return subprocess.run(cmd, shell=shell, capture_output=True, text=True)

def get_agents_from_container():
    print("⬇️  Copying CheckMK Agents from nexi-checkmk container...")
    
    # Verified Paths
    base_path = "/opt/omd/sites/nexi_monitor/share/check_mk/agents"
    deb_name = "check-mk-agent_2.2.0p47-1_all.deb"
    rpm_name = "check-mk-agent-2.2.0p47-1.noarch.rpm"
    
    print(f"  - Copying DEB: {deb_name}")
    res_deb = run_cmd(f"docker cp nexi-checkmk:{base_path}/{deb_name} agent.deb")
    
    print(f"  - Copying RPM: {rpm_name}")
    res_rpm = run_cmd(f"docker cp nexi-checkmk:{base_path}/{rpm_name} agent.rpm")
    
    if res_deb.returncode != 0:
        print(f"❌ Failed to copy DEB: {res_deb.stderr}")
        return False
        
    return True

def install_on_postgres(container):
    print(f"📦 Installing Agent on Postgres: {container}")
    
    # Check if container exists/running
    check = run_cmd(["docker", "inspect", container])
    if check.returncode != 0:
        print(f"  ⚠️ Container {container} NOT FOUND. Skipping.")
        return

    # Copy agent
    run_cmd(f"docker cp agent.deb {container}:/tmp/agent.deb", shell=True)
    
    # Install xinetd (Debian)
    print("  - Installing xinetd...")
    run_cmd(["docker", "exec", "-u", "0", container, "apt-get", "update"])
    run_cmd(["docker", "exec", "-u", "0", container, "apt-get", "install", "-y", "xinetd"])
    
    # Install Agent
    print("  - Installing agent package...")
    res = run_cmd(["docker", "exec", "-u", "0", container, "dpkg", "-i", "/tmp/agent.deb"])
    
    if res.returncode != 0:
        print(f"  ❌ Installation failed: {res.stderr[:200]}")
    else:
        print(f"  ✅ Agent installed.")
        
    # Start xinetd
    run_cmd(["docker", "exec", "-u", "0", container, "service", "xinetd", "start"])

def install_on_oracle(container):
    print(f"📦 Installing Agent on Oracle: {container}")
    
    check = run_cmd(["docker", "inspect", container])
    if check.returncode != 0:
        print(f"  ⚠️ Container {container} NOT FOUND. Skipping.")
        return

    # Copy agent
    run_cmd(f"docker cp agent.rpm {container}:/tmp/agent.rpm", shell=True)
    
    # Install xinetd (Oracle Linux)
    print("  - Installing xinetd...")
    # Oracle Free might use microdnf
    run_cmd(["docker", "exec", "-u", "0", container, "microdnf", "install", "-y", "xinetd", "findutils"])

    # Install Agent
    print("  - Installing agent RPM...")
    res = run_cmd(["docker", "exec", "-u", "0", container, "rpm", "-Uvh", "/tmp/agent.rpm"])
    
    if res.returncode != 0 and "already installed" not in res.stderr:
        print(f"  ❌ Installation failed: {res.stderr[:200]}")
    else:
        print(f"  ✅ Agent installed.")
        
    # Start xinetd
    run_cmd(["docker", "exec", "-u", "0", container, "xinetd"])

def main():
    if not get_agents_from_container():
        return
    
    print("\n--- Deploying to PostgreSQL ---")
    for c in PG_CONTAINERS:
        install_on_postgres(c)
        
    print("\n--- Deploying to Oracle ---")
    for c in ORA_CONTAINERS:
        install_on_oracle(c)

if __name__ == "__main__":
    main()
