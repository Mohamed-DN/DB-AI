"""
Ingestion Worker - Consumes Redis Queues and updates MongoDB.

This worker facilitates the Async Architecture by Decoupling Agents from the Database.
Agents push to Redis -> IngestionWorker writes to Mongo.
"""
import sys
import os
import time
import json
import logging
from threading import Thread

# Add root path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from api_agents.shared.redis_client import RedisClient
from api_agents.shared.sync_mongo_service import SyncMongoService

# Reuse CMDBUpdater logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../Collector')))
try:
    from src.cmdb_updater import CMDBUpdater
except ImportError:
    logging.warning("Could not import CMDBUpdater from Collector. Ensure paths are correct.")
    CMDBUpdater = None

# Provisioner for Discovery
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../Scout')))
try:
    from user_provisioner import UserProvisioner
except ImportError:
    logging.warning("Could not import UserProvisioner from Scout.")
    UserProvisioner = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("IngestionWorker")

class IngestionWorker:
    def __init__(self):
        self.redis = RedisClient.get_instance()
        self.mongo = SyncMongoService.get_instance()
        
        # Initialize CMDBUpdater if available
        if CMDBUpdater:
            self.cmdb_updater = CMDBUpdater(mongo_proxy=None)
        else:
            self.cmdb_updater = None

        # Initialize Provisioner
        if UserProvisioner:
            self.provisioner = UserProvisioner(self.mongo)
        else:
            self.provisioner = None
            
        self.running = True

    def start(self):
        """Start consumer threads"""
        logger.info("🚀 Starting Ingestion Worker...")
        
        threads = [
            Thread(target=self.process_cmdb_updates, name="CMDB-Worker"),
            Thread(target=self.process_status_updates, name="Status-Worker"),
            Thread(target=self.process_metrics_updates, name="Metrics-Worker"),
            Thread(target=self.process_discovery_updates, name="Discovery-Worker")
        ]
        
        for t in threads:
            t.daemon = True
            t.start()
            
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Stopping Ingestion Worker...")
            self.running = False
            
    def process_discovery_updates(self):
        """Consume DISCOVERY_UPDATES queue"""
        logger.info("Listening on DISCOVERY_UPDATES queue...")
        while self.running:
            try:
                msg = self.redis.pop_from_queue("DISCOVERY_UPDATES", timeout=5)
                if msg:
                    dbs = msg.get('dbs', [])
                    if dbs:
                        self.update_inventory(dbs)
            except Exception as e:
                logger.error(f"Error in Discovery worker: {e}")
                time.sleep(1)

    def update_inventory(self, dbs):
        """Update MongoDB Inventory (Migrated from ScoutAgent)"""
        logger.info(f"💾 Updating Inventory with {len(dbs)} databases...")
        
        # Get existing DBs with status using native PyMongo
        existing_status = self.mongo.get_existing_databases()
        existing_names = set(existing_status.keys())
        
        found_names = set()
        for db in dbs:
            name = db.get('identity', {}).get('db_unique_name')
            if not name: continue
            found_names.add(name)
            
            # Check if NEW
            if name not in existing_names:
                logger.info(f"✨ NEW DATABASE FOUND: {name}")
                alert = {
                    "severity": "WARNING",
                    "state": "WARNING",
                    "type": "NEW_DB_DISCOVERED",
                    "host_name": db['identity'].get('host', 'Unknown'),
                    "service": f"{db['identity']['engine']}-{name}",
                    "message": f"Scout discovered new {db['identity']['engine']} database: {name}",
                    "output": "New Asset",
                    "timestamp": "NOW",
                    "processed": False
                }
                self.mongo.insert_alert(alert)
                
                # 🔑 AUTO-PROVISION AIAUTO USER
                if self.provisioner:
                    try:
                        prov_result = self.provisioner.provision_database(db)
                        if prov_result.get('provisioned'):
                            logger.info(f"✅ AIAUTO user provisioned on {name}")
                        elif prov_result.get('skipped'):
                            logger.info(f"⏭️ Skipped provisioning for {name}: {prov_result.get('reason')}")
                        else:
                            logger.warning(f"⚠️ Provisioning failed for {name}: {prov_result.get('message', prov_result.get('error'))}")
                    except Exception as prov_err:
                        logger.error(f"❌ Provisioning error for {name}: {prov_err}")

            # Check if NEW or EXISTING for Update Logic
            if name in existing_names:
                # EXISTING: Check for RECOVERY
                prev_status = existing_status.get(name, 'UNKNOWN')
                if prev_status in ['MISSING', 'DOWN']:
                    logger.info(f"🎉 RECOVERY DETECTED: {name} is back UP (was {prev_status})")
                    alert = {
                        "severity": "RESOLVED",
                        "state": "RESOLVED", 
                        "type": "DB_RECOVERY",
                        "db_unique_name": name,
                        "host_name": db['identity'].get('host'),
                        "service": f"{db['identity']['engine']}-{name}",
                        "message": f"Database {name} has recovered and is back ONLINE.",
                        "output": "Service Restored",
                        "timestamp": "NOW",
                        "processed": False
                    }
                    self.mongo.insert_alert(alert)

                # EXISTING: Only update state/status, preserve manual metadata
                self.mongo.update_last_seen(name, "UP")
            else:
                # NEW: Full Upsert - Merge document with state fields
                if 'state' not in db: db['state'] = {}
                db['state']['status'] = 'UP'
                db['state']['last_seen'] = datetime.utcnow()
                self.mongo.upsert_database(db)
        
        # Check MISSING - but exclude REMOTE databases
        remote_names = set(self.mongo.get_remote_databases())
        
        missing_names = existing_names - found_names - remote_names
        for missing in missing_names:
            prev_status = existing_status.get(missing, 'UNKNOWN')
            
            # Update status to MISSING
            self.mongo.update_last_seen(missing, "MISSING")
            
            # Anti-Spam: Only alert if it's a NEW incident
            if prev_status != 'MISSING':
                logger.warning(f"⚠️ DETECTED MISSING ASSET: {missing} (Prev: {prev_status})")
                
                # Create Alert
                alert = {
                    "severity": "CRITICAL",
                    "state": "CRITICAL",
                    "type": "ASSET_MISSING",
                    "db_unique_name": missing,
                    "host_name": "Docker",
                    "service": f"DB-{missing}",
                    "message": f"Database {missing} was not found in Docker scan.",
                    "output": "Container Missing",
                    "timestamp": "NOW",
                    "processed": False
                }
                self.mongo.insert_alert(alert)


    def process_cmdb_updates(self):
        """Consume CMDB_UPDATES queue"""
        logger.info("Listening on CMDB_UPDATES queue...")
        while self.running:
            try:
                msg = self.redis.pop_from_queue("CMDB_UPDATES", timeout=5)
                if msg:
                    logger.info(f"💾 Processing CMDB update for {msg.get('identity', {}).get('db_unique_name')}")
                    if self.cmdb_updater:
                        self.cmdb_updater.upsert_database(msg)
                    else:
                        # Direct fallback if updater missing
                        self.mongo.db.inventory_databases.update_one(
                             {"identity.db_unique_name": msg.get("identity", {}).get("db_unique_name")},
                             {"$set": msg},
                             upsert=True
                        )
            except Exception as e:
                logger.error(f"Error in CMDB worker: {e}")
                time.sleep(1)

    def process_status_updates(self):
        """Consume STATUS_UPDATES queue"""
        logger.info("Listening on STATUS_UPDATES queue...")
        while self.running:
            try:
                msg = self.redis.pop_from_queue("STATUS_UPDATES", timeout=5)
                if msg:
                    name = msg.get("name")
                    status = msg.get("status")
                    if name and status:
                        logger.debug(f"🚦 Status update: {name} -> {status}")
                        self.mongo.update_status(name, status)
            except Exception as e:
                logger.error(f"Error in Status worker: {e}")
                time.sleep(1)

    def process_metrics_updates(self):
        """Consume METRICS_UPDATES queue"""
        logger.info("Listening on METRICS_UPDATES queue...")
        while self.running:
            try:
                msg = self.redis.pop_from_queue("METRICS_UPDATES", timeout=5)
                if msg:
                    name = msg.get("name")
                    metrics = msg.get("metrics")
                    if name and metrics:
                        logger.debug(f"📊 Metrics update for {name}")
                        self.mongo.update_metrics(name, metrics)
            except Exception as e:
                logger.error(f"Error in Metrics worker: {e}")
                time.sleep(1)

if __name__ == "__main__":
    worker = IngestionWorker()
    worker.start()
