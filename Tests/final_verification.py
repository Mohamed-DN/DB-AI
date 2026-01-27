import urllib.request
import urllib.error
import subprocess
import sys

def check_url(url, name):
    try:
        resp = urllib.request.urlopen(url, timeout=5)
        print(f"✅ {name} is reachable ({resp.getcode()})")
        return True
    except Exception as e:
        print(f"❌ {name} is unreachable: {e}")
        return False

def check_docker_containers():
    print("\n🐳 Checking Docker Containers...")
    try:
        output = subprocess.check_output(["docker", "ps", "--format", "{{.Names}}"]).decode()
        required = [
            "nexi-frontend", 
            "nexi-backend", 
            "nexi-celery-worker", 
            "nexi-oem-collector", 
            "nexi-sentinel-predictor",
            "nexi-mongodb2",
            "nexi-redis-core",
            "nexi-victoriametrics"
        ]
        all_up = True
        for r in required:
            if r in output:
                print(f"✅ Container {r} is UP")
            else:
                print(f"❌ Container {r} is DOWN")
                all_up = False
        return all_up
    except Exception as e:
        print(f"❌ Docker check failed: {e}")
        return False

def main():
    print("🚀 Starting Final System Verification...")
    
    # 1. Container Check
    containers_ok = check_docker_containers()
    
    print("\n🌐 Checking Network Endpoints...")
    # 2. Frontend Check
    check_url("http://localhost:4002", "Frontend")
    
    # 3. Backend Health Check
    # /health not explicitly in router list, but usually there. Trying root or /docs if /health fails
    if not check_url("http://localhost:8000/docs", "Backend API Docs"):
         print("   (Backend might be starting up or port is wrong)")
    
    # 4. Agent Registry Check
    try:
        resp = urllib.request.urlopen("http://localhost:8000/api/agents", timeout=5)
        print(f"✅ Agent Registry is accessible ({resp.getcode()})")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(f"✅ Agent Registry is protected (401 Unauthorized) - Auth working")
        elif e.code == 404:
             print(f"⚠️ Agent Registry endpoint not found (404)")
        else:
            print(f"❌ Agent Registry error: {e}")
    except Exception as e:
        print(f"❌ Agent Registry unreachable: {e}")

    # 5. VictoriaMetrics Check
    check_url("http://localhost:8428/health", "VictoriaMetrics")

    if containers_ok:
        print("\n✅ System seems OPERATIONAL.")
        sys.exit(0)
    else:
        print("\n⚠️ System has issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()
