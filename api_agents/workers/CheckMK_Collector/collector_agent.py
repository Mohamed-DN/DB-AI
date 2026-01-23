"""
Centralized CheckMK Collector Agent
====================================
Runs on the central MongoDB machine and collects data from ALL CheckMK Raw instances
distributed across the database servers.

Architecture:
┌──────────────────────────────────────────────────────────────────┐
│                    Central MongoDB Machine                        │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              CheckMK Collector Agent                      │    │
│  │  ┌────────────────────────────────────────────────────┐  │    │
│  │  │ Poll CheckMK REST API from each DB machine         │  │    │
│  │  │ - Milano: http://10.0.1.10:8080/cmk_api            │  │    │
│  │  │ - Cairo: http://10.0.2.10:8080/cmk_api             │  │    │
│  │  │ - Bratislava: http://10.0.3.10:8080/cmk_api        │  │    │
│  │  └────────────────────────────────────────────────────┘  │    │
│  │              ↓                    ↓                        │    │
│  │     ┌───────────────┐    ┌───────────────┐               │    │
│  │     │   MongoDB     │    │VictoriaMetrics│               │    │
│  │     │  (Inventory)  │    │   (Metrics)   │               │    │
│  │     └───────────────┘    └───────────────┘               │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘

Features:
- Multi-site polling (no plugins needed on CheckMK machines)
- Parallel collection for performance
- Writes inventory to MongoDB
- Exports metrics to VictoriaMetrics via Graphite or Prometheus format
- Configurable via YAML or environment variables
"""

import os
import time
import json
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

import requests
from pymongo import MongoClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CheckMK_Collector")


@dataclass
class CheckMKInstance:
    """Represents a CheckMK instance to poll"""
    name: str
    url: str
    site: str
    username: str
    password: str
    datacenter: str = "unknown"
    target_hosts: List[str] = field(default_factory=list)
    enabled: bool = True
    # Multi-protocol support for CheckMK 1.5.x legacy
    api_mode: str = "rest_api"  # rest_api | livestatus | webapi_legacy
    api_version: str = "2.x"    # 1.5.0p16, 2.x, etc.
    livestatus_host: Optional[str] = None
    livestatus_port: int = 6557
    automation_secret: Optional[str] = None


@dataclass
class CollectorConfig:
    """Main configuration for the collector"""
    # CheckMK instances to poll
    instances: List[CheckMKInstance] = field(default_factory=list)
    
    # MongoDB settings
    mongo_uri: str = "mongodb://admin:nexi2024@localhost:28017/"
    mongo_db: str = "nexi_cmdb_v2"
    
    # VictoriaMetrics Graphite endpoint
    graphite_host: str = "localhost"
    graphite_port: int = 2003
    
    # Polling settings
    poll_interval_seconds: int = 60
    request_timeout: int = 30
    max_workers: int = 5


# =============================================================================
# Default Configuration (for development/testing)
# =============================================================================

def discover_checkmk_from_gateways(mongo_uri: str, mongo_db: str) -> List[CheckMKInstance]:
    """
    Discover CheckMK instances AND target hosts from the gateway collection in MongoDB.
    Supports multi-protocol: REST API (2.x), Livestatus (1.5.x), Web API Legacy (1.5.x)
    """
    instances = []
    
    try:
        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        
        # Get all gateways
        gateways = list(db.gateways.find({"enabled": {"$ne": False}}))
        
        logger.info(f"📡 Discovered {len(gateways)} gateways from MongoDB")
        
        for gw in gateways:
            gw_id = gw.get("_id", "unknown")
            datacenter = gw.get("datacenter", gw.get("location", "unknown"))
            checkmk_port = gw.get("checkmk_port", 8080)
            checkmk_site = gw.get("checkmk_site", "nexi_monitor")
            checkmk_user = gw.get("checkmk_user", os.getenv("CHECKMK_USER", "cmkadmin"))
            checkmk_pass = gw.get("checkmk_password", os.getenv("CHECKMK_PASSWORD", "nexi2024"))
            
            # Multi-protocol support fields
            checkmk_version = gw.get("checkmk_version", "2.x")
            api_mode = gw.get("checkmk_api_mode", "rest_api")  # rest_api | livestatus | webapi_legacy
            livestatus_port = gw.get("checkmk_livestatus_port", 6557)
            automation_secret = gw.get("checkmk_automation_secret")
            
            # Auto-detect: if version is 1.x and no api_mode specified, default to livestatus
            if checkmk_version.startswith("1.") and api_mode == "rest_api":
                logger.info(f"  ⚙️ Gateway {gw_id} has CheckMK {checkmk_version}, auto-switching to livestatus mode")
                api_mode = "livestatus"
            
            # Get the gateway host IP from ssh_config
            ssh_config = gw.get("ssh_config", {})
            gw_host = ssh_config.get("host") or gw.get("host", "")
            
            # Extract target hosts from the gateway document
            # The structure is: "hosts": [ { "host": "IP", "db_name": "NAME" }, ... ]
            raw_hosts = gw.get("hosts", [])
            target_hosts = []
            for h in raw_hosts:
                # We collect possible identifiers that CheckMK might use
                if h.get("host"): target_hosts.append(h.get("host"))
                if h.get("db_unique_name"): target_hosts.append(h.get("db_unique_name"))
                if h.get("hostname"): target_hosts.append(h.get("hostname"))
            
            # Remove duplicates
            target_hosts = list(set(target_hosts))
            
            if not gw_host:
                if raw_hosts:
                    gw_host = raw_hosts[0].get("host", "")
            
            if gw_host:
                instances.append(CheckMKInstance(
                    name=gw_id,
                    url=f"http://{gw_host}:{checkmk_port}",
                    site=checkmk_site,
                    datacenter=datacenter,
                    username=checkmk_user,
                    password=checkmk_pass,
                    target_hosts=target_hosts,
                    enabled=True,
                    # Multi-protocol fields
                    api_mode=api_mode,
                    api_version=checkmk_version,
                    livestatus_host=gw_host,
                    livestatus_port=livestatus_port,
                    automation_secret=automation_secret or checkmk_pass
                ))
                logger.info(f"  ✅ Added CheckMK: {gw_id} @ {gw_host} (mode={api_mode}, version={checkmk_version})")
                logger.debug(f"     Found {len(target_hosts)} target hosts in Mongo for this gateway")
            else:
                logger.warning(f"  ⚠️ Gateway {gw_id} has no host IP configured")
        
        client.close()
        
    except Exception as e:
        logger.error(f"Error discovering gateways: {e}")
    
    return instances


def get_default_config() -> CollectorConfig:
    """Load configuration strictly from MongoDB gateways"""
    
    mongo_uri = os.getenv("MONGO_URI", "mongodb://admin:nexi2024@localhost:28017/")
    mongo_db = os.getenv("MONGO_DB", "nexi_cmdb_v2")
    
    # ALWAYS try to discover from MongoDB gateways collection
    # This aligns with user requirement: "pescare i nomi delle machine da mongo"
    logger.info("🔄 fetching configuration from MongoDB 'gateways' collection...")
    instances = discover_checkmk_from_gateways(mongo_uri, mongo_db)
    
    if not instances:
        logger.warning("⚠️ No gateways found in MongoDB! Collector will remain idle until gateways are added.")
    
    return CollectorConfig(
        instances=instances,
        mongo_uri=mongo_uri,
        mongo_db=mongo_db,
        graphite_host=os.getenv("GRAPHITE_HOST", "localhost"),
        graphite_port=int(os.getenv("GRAPHITE_PORT", "2003")),
        poll_interval_seconds=int(os.getenv("POLL_INTERVAL", "60")),
        request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
        max_workers=int(os.getenv("MAX_WORKERS", "5"))
    )

# ... (CheckMKClient and GraphiteWriter classes imported from checkmk_clients) ...
# Import multi-protocol client support
try:
    from .checkmk_clients import (
        CheckMKClientFactory, 
        CheckMKInstanceConfig, 
        GraphiteWriter
    )
    MULTI_PROTOCOL_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ checkmk_clients module not found, falling back to REST API only")
    MULTI_PROTOCOL_AVAILABLE = False

# =============================================================================
# Main Collector
# =============================================================================

class CheckMKCollector:
    """Main collector that aggregates data from all CheckMK instances"""
    
    def __init__(self, config: CollectorConfig):
        self.config = config
        self.mongo_client = None
        if MULTI_PROTOCOL_AVAILABLE:
            self.graphite = GraphiteWriter(config.graphite_host, config.graphite_port)
        else:
            self.graphite = None
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
    
    def _get_mongo_db(self):
        """Get MongoDB database connection"""
        if self.mongo_client is None:
            self.mongo_client = MongoClient(self.config.mongo_uri)
        return self.mongo_client[self.config.mongo_db]
    
    def _create_client(self, instance: CheckMKInstance):
        """
        Create appropriate CheckMK client based on api_mode.
        Supports: rest_api (2.x), livestatus (1.5.x), webapi_legacy (1.5.x)
        """
        if not MULTI_PROTOCOL_AVAILABLE:
            # Fallback: basic REST API client
            logger.warning(f"Using basic REST client for {instance.name}")
            return None
        
        # Convert CheckMKInstance to CheckMKInstanceConfig
        client_config = CheckMKInstanceConfig(
            name=instance.name,
            url=instance.url,
            site=instance.site,
            datacenter=instance.datacenter,
            api_mode=instance.api_mode,
            api_version=instance.api_version,
            username=instance.username,
            password=instance.password,
            livestatus_host=instance.livestatus_host,
            livestatus_port=instance.livestatus_port,
            automation_secret=instance.automation_secret,
            timeout=self.config.request_timeout,
            enabled=instance.enabled,
            target_hosts=instance.target_hosts
        )
        
        return CheckMKClientFactory.create(client_config)
    
    def collect_from_instance(self, instance: CheckMKInstance) -> Dict:
        """Collect data from a single CheckMK instance using MongoDB target list"""
        if not instance.enabled:
            return {"instance": instance.name, "hosts": [], "metrics": []}
        
        # Create appropriate client based on api_mode
        client = self._create_client(instance)
        if client is None:
            logger.error(f"Could not create client for {instance.name}")
            return {"instance": instance.name, "hosts": [], "metrics": [], "error": "Client creation failed"}
        
        logger.info(f"🔄 Collecting from {instance.name} using {instance.api_mode} mode (CheckMK {instance.api_version})")
        
        # We rely on MongoDB as the source of truth for which hosts to extract
        target_hosts_set = set(instance.target_hosts)
        
        services = client.get_all_services_status()
        
        # Filter services: Keep only those belonging to hosts defined in MongoDB
        # If target_hosts is empty, we might defaults to ALL (or NONE depending on strictness)
        # Assuming strict: only what is in Mongo.
        
        filtered_services = []
        discovered_hosts_map = {}
        
        if target_hosts_set:
            for s in services:
                h_name = s.get("host_name")
                if h_name in target_hosts_set:
                    filtered_services.append(s)
                    discovered_hosts_map[h_name] = True
        else:
            # Fallback: if no hosts defined in Mongo gateway, take everything (Legacy behavior?)
            # Or log warning. Let's take everything but log.
            logger.warning(f"  ⚠️ No target hosts defined for {instance.name} in MongoDB. Collecting ALL.")
            filtered_services = services
            for s in services:
                 discovered_hosts_map[s.get("host_name")] = True

        discovered_hosts_list = [{"title": name} for name in discovered_hosts_map.keys()]
        
        logger.info(f"Collected {len(filtered_services)} services from {instance.name} (Matched {len(discovered_hosts_map)}/{len(target_hosts_set)} Mongo hosts)")
        
        # Prepare metrics for Graphite
        metrics = []
        now = int(time.time())
        prefix = f"checkmk.{instance.datacenter}.{instance.name}"
        
        # Host count metric
        metrics.append((f"{prefix}.hosts_total", len(discovered_hosts_list), now))
        
        # Service state counts
        service_states = {"ok": 0, "warn": 0, "crit": 0, "unknown": 0}
        for svc in filtered_services:
            ext = svc.get("extensions", {})
            state = ext.get("state", 3)
            if state == 0:
                service_states["ok"] += 1
            elif state == 1:
                service_states["warn"] += 1
            elif state == 2:
                service_states["crit"] += 1
            else:
                service_states["unknown"] += 1
        
        for state_name, count in service_states.items():
            metrics.append((f"{prefix}.services_{state_name}", count, now))
        
        return {
            "instance": instance.name,
            "datacenter": instance.datacenter,
            "hosts": discovered_hosts_list,
            "services": filtered_services,
            "metrics": metrics,
            "collected_at": datetime.utcnow()
        }
    
    def save_to_mongodb(self, data: Dict):
        """Save collected data to MongoDB inventory"""
        db = self._get_mongo_db()
        
        # We only really need to update 'last_seen' or status since the host comes FROM Mongo
        # But we can enrich with CheckMK data
        
        for host_data in data.get("hosts", []):
            host_name = host_data.get("title")
            if not host_name:
                continue
            
            doc = {
                "identity": {
                    "db_unique_name": host_name,
                    "host": host_data.get("extensions", {}).get("attributes", {}).get("ipaddress", "unknown"),
                    "type": "CheckMK_Host"
                },
                "source": "CheckMK",
                "checkmk_instance": data["instance"],
                "datacenter": data.get("datacenter", "unknown"),
                "last_seen": data["collected_at"],
                "raw_data": host_data
            }
            
            db.inventory_databases.update_one(
                {"identity.db_unique_name": host_name},
                {"$set": doc},
                upsert=True
            )
    
    def send_metrics(self, data: Dict):
        """Send metrics to VictoriaMetrics via Graphite"""
        self.graphite.send_batch(data.get("metrics", []))
    
    def run_once(self):
        """Run a single collection cycle"""
        logger.info(f"Starting collection from {len(self.config.instances)} CheckMK instances...")
        
        # Collect from all instances in parallel
        futures = []
        for instance in self.config.instances:
            future = self.executor.submit(self.collect_from_instance, instance)
            futures.append(future)
        
        # Process results
        total_hosts = 0
        total_services = 0
        total_metrics = 0
        
        for future in futures:
            try:
                data = future.result()
                total_hosts += len(data.get("hosts", []))
                total_services += len(data.get("services", []))
                total_metrics += len(data.get("metrics", []))
                
                # Save to MongoDB
                self.save_to_mongodb(data)
                
                # Send metrics
                self.send_metrics(data)
                
            except Exception as e:
                logger.error(f"Error processing collection result: {e}")
        
        logger.info(f"Collection complete: {total_hosts} hosts, {total_services} services, {total_metrics} metrics")
    
    def run_forever(self):
        """Run continuous collection loop"""
        logger.info("🚀 CheckMK Collector Agent starting...")
        logger.info(f"📡 Polling {len(self.config.instances)} CheckMK instances")
        logger.info(f"💾 MongoDB: {self.config.mongo_uri}")
        logger.info(f"📊 Graphite: {self.config.graphite_host}:{self.config.graphite_port}")
        logger.info(f"⏰ Interval: {self.config.poll_interval_seconds}s")
        
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"Collection cycle error: {e}")
            
            logger.info(f"💤 Sleeping {self.config.poll_interval_seconds}s...")
            time.sleep(self.config.poll_interval_seconds)


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Centralized CheckMK Collector Agent")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--config", type=str, help="Path to config file (YAML/JSON)")
    args = parser.parse_args()
    
    config = get_default_config()
    
    # Load from file if specified
    if args.config:
        # TODO: Load from YAML/JSON file
        pass
    
    collector = CheckMKCollector(config)
    
    if args.once:
        collector.run_once()
    else:
        collector.run_forever()


if __name__ == "__main__":
    main()
