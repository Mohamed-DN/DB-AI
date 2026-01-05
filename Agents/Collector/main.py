"""
SADA Collector Agent - Docker Edition
Collects deep metrics (CPU, RAM, IO) from Docker containers
"""
import sys
import os
import time
import json
import subprocess
from datetime import datetime

# Force UTF-8 for Windows Console
sys.stdout.reconfigure(encoding='utf-8')

# Link to Shared Modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from Orchestrator.src.mongo_proxy import MongoProxy

class CollectorAgent:
    def __init__(self):
        self.mongo = MongoProxy()
        
    def collect_docker_metrics(self, container_name):
        """Collect real-time metrics from Docker"""
        try:
            # Stats command
            cmd = ["docker", "stats", container_name, "--no-stream", "--format", "{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}|{{.NetIO}}|{{.BlockIO}}"]
            output = subprocess.check_output(cmd).decode('utf-8').strip()
            
            if not output: return None
            
            # Docker might return multiple lines if ambiguous, but usually one.
            lines = output.split('\n')
            parts = lines[0].split('|')
            
            return {
                "cpu_usage": parts[0],      # e.g. "0.05%"
                "ram_usage": parts[1],      # e.g. "50MiB / 1GiB"
                "ram_percent": parts[2],    # e.g. "5.00%"
                "net_io": parts[3],         # e.g. "1kB / 2kB"
                "disk_io": parts[4],        # e.g. "0B / 0B"
                "captured_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            # Container might be down
            return None

    def run_once(self):
        print("📊 Collector: Starting metrics gathering cycle...")
        inventory = self.mongo.get_inventory()
        if not inventory:
            print("   Inventory empty. Skipping.")
            return

        count = 0
        for db in inventory:
            # Identity
            name = db.get('identity', {}).get('db_unique_name')
            # Check if likely a container (we use name as container name in this setup)
            # In Scout we set db_unique_name = Container Name.upper()
            # Container Name needed lower usually?
            container_name = db.get('identity', {}).get('db_name') # Added db_name in Scout earlier?
            
            # Fallback if db_name missing (old inventory items)
            if not container_name:
                container_name = name.lower() if name else None
            
            if container_name:
                metrics = self.collect_docker_metrics(container_name)
                if metrics:
                    print(f"   📈 Metrics for {name}: CPU={metrics['cpu_usage']}, RAM={metrics['ram_usage']}")
                    self.mongo.update_metrics(name, metrics)
                    count += 1
                else:
                    print(f"   ⚠️ Could not collect metrics for {name} (Down?)")
        
        print(f"✅ Metric Sync Complete. Updated {count} assets.")

    def run_continuous(self, interval=30):
        print(f"🔄 Collector Agent running continuously (Interval: {interval}s)...")
        while True:
            self.run_once()
            time.sleep(interval)

if __name__ == "__main__":
    agent = CollectorAgent()
    # Check if run once
    if "--once" in sys.argv:
        agent.run_once()
    else:
        agent.run_continuous()
