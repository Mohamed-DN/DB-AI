"""
CheckMK Bridge Agent - Placeholder
This agent syncs Nexi CMDB with CheckMK monitoring.
"""
import argparse
import time
import sys
import os
import logging
import requests
from typing import List, Dict, Any

# Add root path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CheckMKBridge")

class CheckMKBridge:
    def __init__(self, mongo_service=None):
        self.mongo = mongo_service
        self.cmk_url = os.getenv("CHECKMK_URL", "http://checkmk:5000/nexi_monitor/check_mk/api/1.0")
        self.cmk_user = os.getenv("CHECKMK_USER", "cmkadmin")
        self.cmk_password = os.getenv("CHECKMK_PASSWORD", "nexi2024")
        self.site = os.getenv("CHECKMK_SITE", "nexi_monitor")
        self.headers = {
            "Authorization": f"Bearer {self.cmk_user} {self.cmk_password}",
            "Accept": "application/json",
            "Content-Type": "application/json" 
        }

    def get_mongo_hosts(self) -> List[Dict]:
        """Fetch all database hosts from MongoDB inventory"""
        if not self.mongo:
            logger.error("MongoDB service not available")
            return []
        
        try:
            # We want unique hosts, not just DB instances (multiple DBs per host)
            # But simplistic approach: get all DBs and extract hosts
            dbs = self.mongo.list_databases() # Returns list of dicts
            hosts = {}
            for db in dbs:
                host = db.get("connection", {}).get("host")
                if host and host not in hosts:
                    hosts[host] = {
                        "host_name": host,
                        "ip_address": db.get("connection", {}).get("host"), # Assuming host is IP or resolving hostname
                        "attributes": {
                            "tag_agent": "cmk-agent", # Default
                            "tag_criticality": "prod" if "prod" in host else "test"
                        }
                    }
            return list(hosts.values())
        except Exception as e:
            logger.error(f"Failed to fetch hosts from MongoDB: {e}")
            return []

    def sync_to_checkmk(self):
        """Push hosts to CheckMK"""
        mongo_hosts = self.get_mongo_hosts()
        logger.info(f"Found {len(mongo_hosts)} unique hosts in MongoDB")
        
        for host in mongo_hosts:
            self._add_host(host)

        # Trigger Activate Changes
        self._activate_changes()

    def _add_host(self, host_data: Dict):
        """Add a single host to CheckMK"""
        host_name = host_data["host_name"]
        url = f"{self.cmk_url}/domain-types/host_config/collections/all"
        
        payload = {
            "host_name": host_name,
            "folder": "/", 
            "attributes": {
                "ipaddress": host_data["ip_address"],
                **host_data["attributes"]
            }
        }
        
        try:
            # Check if exists first? Or just try create and catch 409
            # CheckMK API usually returns 409 if exists.
            resp = requests.post(url, json=payload, headers=self.headers, verify=False)
            
            if resp.status_code == 200:
                logger.info(f"✅ Added host {host_name} to CheckMK")
            elif resp.status_code == 409:
                logger.debug(f"Host {host_name} already exists in CheckMK")
            else:
                logger.warning(f"Failed to add host {host_name}: {resp.status_code} - {resp.text}")
                
        except Exception as e:
            logger.error(f"Error adding host {host_name}: {e}")

    def _activate_changes(self):
        """Activate accumulated changes in CheckMK"""
        url = f"{self.cmk_url}/domain-types/activation_run/collections/pending_changes"
        payload = {
            "redirect": False,
            "sites": [self.site],
            "force_foreign_changes": False
        }
        
        try:
            resp = requests.post(url, json=payload, headers=self.headers, verify=False)
            if resp.status_code == 200:
                logger.info("✅ Activated CheckMK changes")
            else:
                logger.warning(f"Failed to activate changes: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"Error activating changes: {e}")

    def run_continuous(self, interval: int):
        logger.info(f"BRIDGE STARTED. Sync interval: {interval}s")
        while True:
            try:
                self.sync_to_checkmk()
            except Exception as e:
                logger.error(f"Sync cycle failed: {e}")
            time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=int, default=300)
    args = parser.parse_args()

    try:
        from api_agents.shared.sync_mongo_service import SyncMongoService
        mongo = SyncMongoService.get_instance()
    except Exception as e:
        logger.warning(f"MongoDB not available: {e}")
        mongo = None

    bridge = CheckMKBridge(mongo)
    
    if args.once:
        bridge.sync_to_checkmk()
    else:
        bridge.run_continuous(args.interval)
