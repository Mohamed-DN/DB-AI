"""
OEM Collector Agent - Oracle Enterprise Manager REST API Collector

Fetches database performance metrics from Oracle Enterprise Manager 13c+
and ingests them into VictoriaMetrics for predictive analytics.

Part of the Nexi DBA AI Monitoring System.
"""
import os
import sys
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import httpx

# Add root path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

logger = logging.getLogger("OEMCollector")


@dataclass
class OEMInstance:
    """Oracle Enterprise Manager instance configuration"""
    name: str
    url: str  # e.g., https://oem.nexi.it:7803/em
    username: str
    password: str
    verify_ssl: bool = False


@dataclass
class OEMMetric:
    """Collected metric from OEM"""
    target_name: str
    target_type: str
    metric_name: str
    value: float
    timestamp: datetime
    unit: str = ""
    
    def to_prometheus_format(self) -> Dict[str, Any]:
        """Convert to Prometheus/VictoriaMetrics format"""
        # Create safe metric name
        safe_name = f"oem_{self.metric_name.lower().replace(' ', '_').replace('.', '_')}"
        return {
            "metric": safe_name,
            "labels": {
                "db_name": self.target_name,
                "target_type": self.target_type
            },
            "value": self.value,
            "timestamp": int(self.timestamp.timestamp() * 1000)
        }


class OEMClient:
    """
    REST API client for Oracle Enterprise Manager.
    
    OEM REST API Documentation:
    https://docs.oracle.com/en/enterprise-manager/cloud-control/enterprise-manager-cloud-control/13.5/emcli/
    """
    
    # Key metrics to collect from OEM
    DEFAULT_METRICS = [
        "cpu_usage_percent",
        "memory_usage_percent",
        "active_sessions",
        "wait_time_ratio",
        "response_time",
        "tablespace_used_pct",
        "io_throughput",
        "redo_log_switches",
        "buffer_cache_hit_ratio",
        "shared_pool_free_pct"
    ]
    
    def __init__(self, instance: OEMInstance):
        self.instance = instance
        self.base_url = instance.url.rstrip('/')
        self.auth = (instance.username, instance.password)
        self.session: Optional[httpx.Client] = None
        
    def _get_session(self) -> httpx.Client:
        """Get or create HTTP session"""
        if self.session is None:
            self.session = httpx.Client(
                auth=self.auth,
                verify=self.instance.verify_ssl,
                timeout=30.0,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            )
        return self.session
    
    def close(self):
        """Close HTTP session"""
        if self.session:
            self.session.close()
            self.session = None
    
    def test_connection(self) -> bool:
        """Test OEM connection"""
        try:
            client = self._get_session()
            resp = client.get(f"{self.base_url}/api/v2/")
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"OEM connection test failed: {e}")
            return False
    
    def get_targets(self, target_type: str = "oracle_database") -> List[Dict]:
        """
        Get all targets of specified type.
        
        Args:
            target_type: Type of target (oracle_database, host, etc.)
            
        Returns:
            List of target dictionaries
        """
        try:
            client = self._get_session()
            resp = client.get(
                f"{self.base_url}/api/targets",
                params={"targetType": target_type}
            )
            resp.raise_for_status()
            
            data = resp.json()
            return data.get("items", [])
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get targets: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting targets: {e}")
            return []
    
    def get_target_metrics(
        self,
        target_name: str,
        target_type: str = "oracle_database",
        metric_names: Optional[List[str]] = None
    ) -> List[OEMMetric]:
        """
        Get current metric values for a target.
        
        Args:
            target_name: Name of the target (database name)
            target_type: Type of target
            metric_names: List of metrics to fetch (defaults to all key metrics)
            
        Returns:
            List of OEMMetric objects
        """
        if metric_names is None:
            metric_names = self.DEFAULT_METRICS
            
        metrics = []
        now = datetime.utcnow()
        
        try:
            client = self._get_session()
            
            # OEM API endpoint for metric data
            resp = client.get(
                f"{self.base_url}/api/targets/{target_name}/metrics",
                params={
                    "targetType": target_type,
                    "metricColumns": ",".join(metric_names)
                }
            )
            
            if resp.status_code == 404:
                logger.warning(f"Target {target_name} not found in OEM")
                return []
                
            resp.raise_for_status()
            data = resp.json()
            
            # Parse metric data
            for item in data.get("items", []):
                metric_name = item.get("metricColumn", item.get("name", "unknown"))
                value = item.get("value")
                
                if value is not None:
                    try:
                        metrics.append(OEMMetric(
                            target_name=target_name,
                            target_type=target_type,
                            metric_name=metric_name,
                            value=float(value),
                            timestamp=now,
                            unit=item.get("unit", "")
                        ))
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse metric value: {value}")
            
            return metrics
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get metrics for {target_name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting metrics for {target_name}: {e}")
            return []
    
    def get_historical_metrics(
        self,
        target_name: str,
        metric_name: str,
        hours_back: int = 24,
        target_type: str = "oracle_database"
    ) -> List[OEMMetric]:
        """
        Get historical metric data for trend analysis.
        
        Args:
            target_name: Target name
            metric_name: Metric to fetch
            hours_back: Hours of history to fetch
            target_type: Type of target
            
        Returns:
            List of OEMMetric objects with timestamps
        """
        metrics = []
        
        try:
            client = self._get_session()
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours_back)
            
            resp = client.get(
                f"{self.base_url}/api/targets/{target_name}/metrics/history",
                params={
                    "targetType": target_type,
                    "metricColumn": metric_name,
                    "startTime": start_time.isoformat() + "Z",
                    "endTime": end_time.isoformat() + "Z"
                }
            )
            resp.raise_for_status()
            data = resp.json()
            
            for point in data.get("data", []):
                timestamp = point.get("timestamp")
                value = point.get("value")
                
                if timestamp and value is not None:
                    try:
                        ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        metrics.append(OEMMetric(
                            target_name=target_name,
                            target_type=target_type,
                            metric_name=metric_name,
                            value=float(value),
                            timestamp=ts
                        ))
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Could not parse data point: {e}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting historical metrics: {e}")
            return []


class OEMCollectorAgent:
    """
    OEM Collector Agent - Collects metrics from Oracle Enterprise Manager
    and pushes them to VictoriaMetrics.
    """
    
    def __init__(self, mongo_service=None, vm_client=None):
        self.mongo = mongo_service
        self.vm = vm_client
        self.oem_clients: List[OEMClient] = []
        
        # Load OEM instances from config
        self._load_oem_instances()
    
    def _load_oem_instances(self):
        """Load OEM instances from environment or MongoDB config"""
        # Try environment variables first
        oem_instances_str = os.getenv("OEM_INSTANCES", "")
        
        if oem_instances_str:
            # Format: name1|url1|user1|pass1,name2|url2|user2|pass2
            for instance_str in oem_instances_str.split(","):
                parts = instance_str.strip().split("|")
                if len(parts) >= 4:
                    instance = OEMInstance(
                        name=parts[0],
                        url=parts[1],
                        username=parts[2],
                        password=parts[3],
                        verify_ssl=len(parts) > 4 and parts[4].lower() == "true"
                    )
                    self.oem_clients.append(OEMClient(instance))
                    logger.info(f"Loaded OEM instance: {instance.name} ({instance.url})")
        
        # Also try MongoDB config
        if self.mongo:
            try:
                config = self.mongo.get_config("oem_instances")
                if config and isinstance(config, list):
                    for inst_cfg in config:
                        instance = OEMInstance(
                            name=inst_cfg.get("name", "OEM"),
                            url=inst_cfg.get("url"),
                            username=inst_cfg.get("username"),
                            password=inst_cfg.get("password"),
                            verify_ssl=inst_cfg.get("verify_ssl", False)
                        )
                        # Avoid duplicates
                        if not any(c.instance.url == instance.url for c in self.oem_clients):
                            self.oem_clients.append(OEMClient(instance))
                            logger.info(f"Loaded OEM instance from MongoDB: {instance.name}")
            except Exception as e:
                logger.debug(f"Could not load OEM config from MongoDB: {e}")
        
        if not self.oem_clients:
            logger.warning("No OEM instances configured. Set OEM_INSTANCES env var or add to MongoDB config.")
    
    def collect_from_instance(self, client: OEMClient) -> List[OEMMetric]:
        """Collect all metrics from a single OEM instance"""
        all_metrics = []
        
        try:
            # Get all database targets
            targets = client.get_targets("oracle_database")
            logger.info(f"Found {len(targets)} database targets in {client.instance.name}")
            
            for target in targets:
                target_name = target.get("name") or target.get("targetName")
                if not target_name:
                    continue
                
                # Get current metrics
                metrics = client.get_target_metrics(target_name)
                all_metrics.extend(metrics)
                
                logger.debug(f"Collected {len(metrics)} metrics for {target_name}")
            
        except Exception as e:
            logger.error(f"Error collecting from {client.instance.name}: {e}")
        
        return all_metrics
    
    def push_to_victoriametrics(self, metrics: List[OEMMetric]) -> bool:
        """Push collected metrics to VictoriaMetrics"""
        if not self.vm:
            logger.warning("VictoriaMetrics client not available")
            return False
        
        if not metrics:
            return True
        
        try:
            # Convert to Prometheus format
            prom_metrics = [m.to_prometheus_format() for m in metrics]
            return self.vm.write_prometheus(prom_metrics)
        except Exception as e:
            logger.error(f"Failed to push metrics to VictoriaMetrics: {e}")
            return False
    
    def update_inventory(self, metrics: List[OEMMetric]):
        """Update database inventory with latest metrics"""
        if not self.mongo:
            return
        
        # Group metrics by target
        by_target: Dict[str, List[OEMMetric]] = {}
        for m in metrics:
            if m.target_name not in by_target:
                by_target[m.target_name] = []
            by_target[m.target_name].append(m)
        
        # Update each database in inventory
        for target_name, target_metrics in by_target.items():
            try:
                metrics_dict = {m.metric_name: m.value for m in target_metrics}
                self.mongo.update_metrics(target_name, {
                    "oem_metrics": metrics_dict,
                    "oem_last_collected": datetime.utcnow()
                })
            except Exception as e:
                logger.warning(f"Failed to update inventory for {target_name}: {e}")
    
    def run_once(self) -> Dict[str, Any]:
        """Run single collection cycle"""
        results = {
            "instances_checked": 0,
            "metrics_collected": 0,
            "metrics_pushed": 0,
            "errors": []
        }
        
        all_metrics = []
        
        for client in self.oem_clients:
            results["instances_checked"] += 1
            
            try:
                # Test connection first
                if not client.test_connection():
                    results["errors"].append(f"Cannot connect to {client.instance.name}")
                    continue
                
                # Collect metrics
                metrics = self.collect_from_instance(client)
                all_metrics.extend(metrics)
                results["metrics_collected"] += len(metrics)
                
            except Exception as e:
                results["errors"].append(f"{client.instance.name}: {str(e)}")
            finally:
                client.close()
        
        # Push to VictoriaMetrics
        if all_metrics:
            if self.push_to_victoriametrics(all_metrics):
                results["metrics_pushed"] = len(all_metrics)
            
            # Update inventory
            self.update_inventory(all_metrics)
        
        logger.info(
            f"📊 OEM Collection complete: {results['metrics_collected']} metrics "
            f"from {results['instances_checked']} instances"
        )
        
        return results
    
    def run_continuous(self, interval_seconds: int = 300):
        """Run collector continuously"""
        logger.info(f"🏢 OEM Collector starting (interval: {interval_seconds}s)")
        
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"Collection cycle error: {e}")
            
            time.sleep(interval_seconds)


if __name__ == "__main__":
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="OEM Collector Agent")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=300, help="Collection interval in seconds")
    args = parser.parse_args()
    
    # Initialize services
    try:
        from api_agents.shared.sync_mongo_service import SyncMongoService
        from api_agents.shared.victoriametrics_client import get_victoriametrics_client
        
        mongo = SyncMongoService.get_instance()
        vm = get_victoriametrics_client()
    except Exception as e:
        logger.warning(f"Could not initialize services: {e}")
        mongo = None
        vm = None
    
    agent = OEMCollectorAgent(mongo_service=mongo, vm_client=vm)
    
    if args.once:
        result = agent.run_once()
        print(f"\n📊 OEM Collection Results:")
        for k, v in result.items():
            print(f"  {k}: {v}")
    else:
        agent.run_continuous(args.interval)
