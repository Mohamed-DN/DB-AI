"""
CheckMK Simulator - Populates local CheckMK with 2000+ mock hosts
"""
import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:8080/m-dn_monitor/check_mk/api/1.0"
USERNAME = "cmkadmin"
PASSWORD = "pippopippo_1234"
HEADERS = {
    "Authorization": f"Bearer {USERNAME} {PASSWORD}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def wait_for_checkmk():
    print("⏳ Waiting for CheckMK to be ready...")
    for _ in range(30):
        try:
            requests.get(f"{BASE_URL}/domain-types/host_config/collections/all", headers=HEADERS)
            print("✅ CheckMK is ready!")
            return True
        except:
            time.sleep(2)
    return False

def create_host(i):
    regions = ["milano", "bratislava", "cairo", "london", "frankfurt"]
    envs = ["prod", "dev", "stg", "dr"]
    types = ["oracle", "postgres", "mongo", "mysql"]
    
    region = random.choice(regions)
    env = random.choice(envs)
    db_type = random.choice(types)
    host_name = f"m-dn-{db_type}-{region}-{env}-{i:04d}"
    
    payload = {
        "folder": "/",
        "host_name": host_name,
        "attributes": {
            "alias": f"Simulated DB {i}",
            "ipaddress": f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "tag_agent": "no-agent",  # We simulate results via API
        }
    }
    
    try:
        resp = requests.post(
            f"{BASE_URL}/domain-types/host_config/collections/all",
            json=payload,
            headers=HEADERS
        )
        if resp.status_code == 200:
            return True
        else:
            print(f"Failed {host_name}: {resp.text}")
            return False
    except Exception as e:
        print(f"Error {host_name}: {e}")
        return False

def activate_changes():
    print("🔄 Activating changes...")
    resp = requests.post(
        f"{BASE_URL}/domain-types/activation_run/actions/activate-changes/invoke",
        json={"redirect": False, "force_foreign_changes": True},
        headers=HEADERS
    )
    print(f"Activation result: {resp.status_code}")

def main():
    if not wait_for_checkmk():
        print("❌ CheckMK unreachable. Is docker container running?")
        return

    print("🚀 Starting population of 2000 hosts...")
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(create_host, range(1, 2001)))
        
    success = sum(results)
    print(f"✅ Created {success} hosts.")
    
    activate_changes()

if __name__ == "__main__":
    main()
