"""
Register Real Hosts in CheckMK
"""
import requests
import subprocess
import json

BASE_URL = "http://localhost:8080/nexi_monitor/check_mk/api/1.0"
HEADERS = {
    "Authorization": "Bearer cmkadmin nexi2024",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

CONTAINERS = [
    "nexi-pg-milano-prod2", "nexi-pg-milano-dev2", 
    "nexi-pg-bratislava-prod2", "nexi-pg-bratislava-dev2",
    "nexi-oracle-cairo-primary2", "nexi-oracle-cairo-replica2",
    "nexi-mongodb2", "nexi-ollama2"
]

def get_ip(container):
    cmd = ["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", container]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout.strip()

def register_host(name, ip):
    print(f"Adding {name} ({ip})...")
    payload = {
        "folder": "/",
        "host_name": name,
        "attributes": {
            "ipaddress": ip,
            "tag_agent": "cmk-agent", # Real agent!
        }
    }
    
    # Try creating
    resp = requests.post(f"{BASE_URL}/domain-types/host_config/collections/all", json=payload, headers=HEADERS)
    if resp.status_code == 200:
        print("  ✅ Registered.")
    elif resp.status_code == 409:
        print("  ⚠️ Already exists.")
    else:
        print(f"  ❌ Failed: {resp.text}")

def activate():
    print("🔄 Activating changes...")
    requests.post(
        f"{BASE_URL}/domain-types/activation_run/actions/activate-changes/invoke",
        json={"redirect": False, "force_foreign_changes": True},
        headers=HEADERS
    )

def main():
    for c in CONTAINERS:
        ip = get_ip(c)
        if ip:
            register_host(c, ip)
        else:
            print(f"Skipping {c} (No IP)")
            
    activate()

if __name__ == "__main__":
    main()
