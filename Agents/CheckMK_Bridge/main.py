"""
CheckMK Bridge Agent - Ingests External Monitoring Metrics into CMDB
Polls CheckMK REST API and enriches inventory_databases with external_metrics.
"""

import sys
import os
import time
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional

# Fix encoding
sys.stdout.reconfigure(encoding='utf-8')

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from Orchestrator.src.mongo_proxy import MongoProxy


class CheckMKBridge:
    """
    Bridge between CheckMK and the CMDB.
    
    Workflow:
    1. Authenticate with CheckMK API
    2. Fetch host/service states for database hosts
    3. Map CheckMK hosts to CMDB db_unique_name
    4. Update deep_observability.external_metrics.checkmk
    """
    
    def __init__(self, poll_interval: int = 60):
        self.mongo = MongoProxy()
        self.poll_interval = poll_interval
        
        # CheckMK Configuration
        self.checkmk_url = os.getenv("CHECKMK_URL", "http://localhost:5001/check_mk/api/v0")
        self.checkmk_user = os.getenv("CHECKMK_USER", "automation")
        self.checkmk_secret = os.getenv("CHECKMK_SECRET", "")
        
        # Host name mapping: CheckMK hostname -> CMDB db_unique_name
        # In production, this would be dynamic via tags or custom attributes
        self.host_mapping = {
            "nexi-oracle-cairo-primary": "NEXI-ORACLE-CAIRO-PRIMARY",
            "nexi-oracle-cairo-replica": "NEXI-ORACLE-CAIRO-REPLICA",
            "nexi-pg-milano-prod": "NEXI-PG-MILANO-PROD",
            "nexi-pg-milano-dev": "NEXI-PG-MILANO-DEV",
            "nexi-pg-bratislava-prod": "NEXI-PG-BRATISLAVA-PROD",
            "nexi-pg-bratislava-dev": "NEXI-PG-BRATISLAVA-DEV",
            "nexi-pg-milano-stg": "NEXI-PG-MILANO-STG"
        }
    
    def _get_auth_headers(self) -> Dict:
        """Build authentication headers for CheckMK API"""
        return {
            "Authorization": f"Bearer {self.checkmk_user} {self.checkmk_secret}",
            "Accept": "application/json"
        }
    
    def fetch_host_states(self) -> List[Dict]:
        """
        Fetch host states from CheckMK.
        
        Returns list of host state dictionaries.
        """
        # If CheckMK is not configured, return simulated data
        if not self.checkmk_secret:
            return self._simulate_host_states()
        
        try:
            url = f"{self.checkmk_url}/domain-types/host/collections/all"
            response = requests.get(url, headers=self._get_auth_headers(), timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get("value", [])
            
        except requests.exceptions.ConnectionError:
            print("   ⚠️ CheckMK not reachable, using simulated data")
            return self._simulate_host_states()
        except Exception as e:
            print(f"   ❌ CheckMK API Error: {e}")
            return []
    
    def fetch_service_metrics(self, hostname: str) -> Dict:
        """
        Fetch specific metrics for a host (CPU, Memory, Disk).
        
        In real CheckMK, this would query specific services.
        """
        if not self.checkmk_secret:
            return self._simulate_metrics(hostname)
        
        try:
            # Query services for the host
            url = f"{self.checkmk_url}/domain-types/service/collections/all"
            params = {"host_name": hostname}
            response = requests.get(url, headers=self._get_auth_headers(), 
                                   params=params, timeout=10)
            response.raise_for_status()
            
            services = response.json().get("value", [])
            
            # Extract relevant metrics
            metrics = {}
            for svc in services:
                name = svc.get("title", "")
                if "CPU" in name:
                    metrics["cpu_util"] = svc.get("last_output", "")
                elif "Memory" in name or "RAM" in name:
                    metrics["memory_util"] = svc.get("last_output", "")
                elif "Disk" in name or "Filesystem" in name:
                    metrics["disk_util"] = svc.get("last_output", "")
            
            return metrics
            
        except:
            return self._simulate_metrics(hostname)
    
    def _simulate_host_states(self) -> List[Dict]:
        """Generate simulated host state data for testing"""
        import random
        
        states = []
        for host, db_name in self.host_mapping.items():
            states.append({
                "id": host,
                "title": host,
                "state": random.choice(["OK", "OK", "OK", "WARN"]),  # Mostly OK
                "last_check": datetime.now().isoformat()
            })
        return states
    
    def _simulate_metrics(self, hostname: str) -> Dict:
        """Generate simulated metrics"""
        import random
        return {
            "cpu_util": random.randint(5, 85),
            "memory_util": random.randint(30, 90),
            "disk_util": random.randint(20, 75),
            "network_io_mb": random.uniform(0.1, 50.0)
        }
    
    def update_cmdb(self, db_name: str, checkmk_data: Dict) -> bool:
        """
        Update CMDB with CheckMK metrics.
        
        Writes to: deep_observability.external_metrics.checkmk
        """
        checkmk_data["last_sync"] = datetime.now().isoformat()
        checkmk_data["source"] = "CheckMK"
        
        data_json = json.dumps(checkmk_data)
        
        js_cmd = f"""
        db.inventory_databases.updateOne(
            {{ "identity.db_unique_name": "{db_name}" }},
            {{ $set: {{ "deep_observability.external_metrics.checkmk": {data_json} }} }}
        )
        """
        
        result = self.mongo.execute_eval(js_cmd)
        return result is not None
    
    def run_once(self) -> int:
        """Single sync cycle. Returns count of updated databases."""
        print(f"📡 CheckMK Bridge: Syncing external metrics...")
        
        host_states = self.fetch_host_states()
        
        if not host_states:
            print("   No host data retrieved.")
            return 0
        
        updated = 0
        for host in host_states:
            hostname = host.get("id") or host.get("title", "")
            db_name = self.host_mapping.get(hostname)
            
            if not db_name:
                continue  # Not a mapped database host
            
            # Get detailed metrics
            metrics = self.fetch_service_metrics(hostname)
            
            # Combine state and metrics
            checkmk_data = {
                "host_state": host.get("state", "UNKNOWN"),
                "last_check": host.get("last_check"),
                **metrics
            }
            
            if self.update_cmdb(db_name, checkmk_data):
                print(f"   ✅ {db_name}: state={checkmk_data['host_state']}, CPU={metrics.get('cpu_util', 'N/A')}%")
                updated += 1
        
        print(f"   📊 Updated {updated} databases with CheckMK metrics")
        return updated
    
    def run_continuous(self):
        """Continuous sync loop"""
        print(f"📡 CheckMK Bridge started (Poll interval: {self.poll_interval}s)")
        print(f"   Target: {self.checkmk_url}")
        print(f"   Mapped hosts: {len(self.host_mapping)}")
        
        while True:
            try:
                self.run_once()
                time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                print("\n⏹️ Bridge stopped")
                break
            except Exception as e:
                print(f"❌ Error in sync loop: {e}")
                time.sleep(30)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="CheckMK Bridge Agent")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=60, help="Poll interval in seconds")
    args = parser.parse_args()
    
    bridge = CheckMKBridge(poll_interval=args.interval)
    
    if args.once:
        count = bridge.run_once()
        print(f"\n📊 Synced {count} databases")
    else:
        bridge.run_continuous()


if __name__ == "__main__":
    main()
