"""
CheckMK Bridge Worker
Syncs hosts and alerts from CheckMK (Production/Simulation) to MongoDB.
"""
import os
import time
import requests
import logging
from ..base_worker import BaseWorker
from api_agents.api_gateway.services.mongo_service import MongoService

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CheckMK_Bridge")

class CheckMKBridge(BaseWorker):
    def __init__(self):
        super().__init__("CheckMK_Bridge")
        self.base_url = os.getenv("CHECKMK_URL", "http://localhost:8080/nexi_monitor/check_mk/api/1.0")
        self.username = os.getenv("CHECKMK_USER", "cmkadmin")
        self.password = os.getenv("CHECKMK_PASSWORD", "nexi2024")
        self.mongo = MongoService()
        
        self.headers = {
            "Authorization": f"Bearer {self.username} {self.password}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def run(self):
        logger.info("🚀 Starting CheckMK Bridge Sync...")
        while True:
            try:
                await self.sync_hosts()
                await self.sync_alerts()
                logger.info("💤 Sleeping for 60 seconds...")
                time.sleep(60)
            except Exception as e:
                logger.error(f"❌ Sync Error: {e}")
                time.sleep(30)

    async def sync_hosts(self):
        """Sync All Hosts from CheckMK to Inventory"""
        logger.info("🔄 Syncing Hosts...")
        try:
            resp = requests.get(
                f"{self.base_url}/domain-types/host_config/collections/all",
                headers=self.headers
            )
            if resp.status_code != 200:
                logger.error(f"Failed to fetch hosts: {resp.text}")
                return

            hosts = resp.json().get("value", [])
            logger.info(f"📥 Fetched {len(hosts)} hosts from CheckMK")
            
            # Batch upsert to MongoDB
            for host in hosts:
                db_name = host.get("title")  # or host.get("id")
                
                # Filter: Only sync Nexi containers
                if not db_name or not db_name.lower().startswith("nexi-"):
                    continue

                attrs = host.get("extensions", {})
                ip_addr = attrs.get("attributes", {}).get("ipaddress", "unknown")
                
                # Determine engine
                engine = "unknown"
                if "pg" in db_name.lower(): engine = "POSTGRES"
                elif "oracle" in db_name.lower(): engine = "ORACLE"
                elif "mongo" in db_name.lower(): engine = "MONGODB"
                elif "redis" in db_name.lower(): engine = "REDIS"
                
                doc = {
                    "identity": {
                        "db_unique_name": db_name,
                        "host": ip_addr,
                        "engine": engine,
                        "type": engine
                    },
                    "source": "CheckMK",
                    "last_seen": time.time(),
                    "status": "monitored"
                }
                
                # Atomic Upsert
                await self.mongo.db.inventory_databases.update_one(
                    {"identity.db_unique_name": db_name},
                    {"$set": doc},
                    upsert=True
                )
            
            logger.info("✅ Hosts Sync Complete")

        except Exception as e:
            logger.error(f"Host sync failed: {e}")

    async def sync_alerts(self):
        """Sync Alerts (Services in Critical/Warning)"""
        logger.info("🚨 Syncing Alerts...")
        # CheckMK API for service problems logic would go here
        # For simulation, we might need to query specific view
        pass

if __name__ == "__main__":
    import asyncio
    worker = CheckMKBridge()
    asyncio.run(worker.run())
