"""
OEM Repository Metrics Collector
=================================
Connects to Oracle Enterprise Manager Repository database (SYSMAN schema)
and collects historic metrics from mgmt$* tables.

Metrics are sent to VictoriaMetrics via Graphite protocol and optionally
saved to MongoDB for long-term storage.

Architecture:
┌─────────────────────┐     ┌───────────────────────┐     ┌─────────────────────┐
│  OEM Repository     │     │  OEM Repository       │     │  VictoriaMetrics    │
│  (SYSMAN schema)    │────▶│  Collector            │────▶│  (Graphite :2003)   │
└─────────────────────┘     └───────────────────────┘     └─────────────────────┘

Usage:
    python oem_repository_collector.py --config oem_queries.yaml --once
    python oem_repository_collector.py --discover-from-mongo --interval 300
"""
import os
import socket
import time
import re
import json
import yaml
import logging
import argparse
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("OEMRepositoryCollector")


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class OEMRepositoryConfig:
    """Configuration for OEM Repository connection"""
    host: str = "localhost"
    port: int = 1521
    service_name: str = "EMREP"
    username: str = "sysman"
    password: str = ""
    timeout: int = 60


@dataclass 
class QueryConfig:
    """Configuration for a single OEM query"""
    name: str
    sql: str
    interval: int = 3600  # Default: once per hour
    enabled: bool = True
    metric_prefix: str = "oem"
    dimensions: List[str] = field(default_factory=list)  # Columns to use as dimensions
    metrics: List[str] = field(default_factory=list)  # Columns to use as metric values


@dataclass
class CollectorConfig:
    """Main collector configuration"""
    oem_repository: OEMRepositoryConfig = field(default_factory=OEMRepositoryConfig)
    queries: List[QueryConfig] = field(default_factory=list)
    
    # VictoriaMetrics/Graphite
    graphite_host: str = "localhost"
    graphite_port: int = 2003
    
    # MongoDB (optional)
    mongo_uri: str = ""
    mongo_db: str = "m-dn_cmdb_v2"
    
    # Collection settings
    default_interval: int = 3600


# =============================================================================
# Built-in OEM Queries
# =============================================================================

BUILTIN_QUERIES = [
    QueryConfig(
        name="db_current_size",
        sql="""
SELECT
  target_name,
  TO_CHAR(rollup_timestamp, 'YYYY-MM-DD HH24:MI:SS') as rollup_time,
  allocated_gb,
  used_gb
FROM
  ( SELECT
      target_name,
      rollup_timestamp,
      metric_column,
      maximum,
      ROW_NUMBER() OVER (PARTITION BY target_name, metric_column ORDER BY rollup_timestamp DESC) rn
    FROM
      sysman.mgmt$metric_hourly
    WHERE
      target_guid IN (
        SELECT target_guid FROM sysman.mgmt$target
        WHERE (target_type = 'oracle_database' AND type_qualifier3 != 'RACINST')
           OR target_type = 'rac_database'
      )
      AND metric_name = 'DATABASE_SIZE'
  )
WHERE rn = 1
PIVOT (MAX(maximum) FOR metric_column IN ('USED_GB' as USED_GB, 'ALLOCATED_GB' as ALLOCATED_GB))
ORDER BY target_name
        """,
        interval=3600,
        metric_prefix="oem.db",
        dimensions=["target_name"],
        metrics=["used_gb", "allocated_gb"]
    ),
    
    QueryConfig(
        name="db_memory_sga_pga",
        sql="""
SELECT
  t.target_name,
  t.host_name,
  sga.value as sga_total_mb,
  pga.value as pga_total_mb
FROM
  sysman.mgmt$target t
  JOIN sysman.mgmt$metric_current sga ON (t.target_guid = sga.target_guid)
  JOIN sysman.mgmt$metric_current pga ON (t.target_guid = pga.target_guid)
WHERE
  t.target_type = 'oracle_database'
  AND sga.metric_name = 'memory_usage_sga_pga' AND sga.metric_column = 'sga_total'
  AND pga.metric_name = 'memory_usage_sga_pga' AND pga.metric_column = 'pga_total'
ORDER BY t.target_name
        """,
        interval=3600,
        metric_prefix="oem.db",
        dimensions=["target_name", "host_name"],
        metrics=["sga_total_mb", "pga_total_mb"]
    ),
    
    QueryConfig(
        name="sessions_current",
        sql="""
SELECT
  target_name,
  TO_NUMBER(value) as active_sessions
FROM
  sysman.mgmt$metric_current
WHERE
  metric_name = 'instance_throughput'
  AND metric_column = 'avg_active_sessions'
  AND target_type = 'oracle_database'
ORDER BY target_name
        """,
        interval=300,  # Every 5 minutes
        metric_prefix="oem.db",
        dimensions=["target_name"],
        metrics=["active_sessions"]
    ),
    
    QueryConfig(
        name="tablespace_usage",
        sql="""
SELECT
  target_name,
  key_value as tablespace_name,
  TO_NUMBER(MAX(CASE WHEN metric_column = 'spaceUsed' THEN value END)) as used_mb,
  TO_NUMBER(MAX(CASE WHEN metric_column = 'spaceAllocated' THEN value END)) as allocated_mb,
  ROUND(
    TO_NUMBER(MAX(CASE WHEN metric_column = 'spaceUsed' THEN value END)) /
    NULLIF(TO_NUMBER(MAX(CASE WHEN metric_column = 'spaceAllocated' THEN value END)), 0) * 100,
    2
  ) as used_pct
FROM
  sysman.mgmt$metric_current
WHERE
  metric_name = 'tbspAllocation'
  AND target_type = 'oracle_database'
GROUP BY target_name, key_value
ORDER BY target_name, key_value
        """,
        interval=3600,
        metric_prefix="oem.db",
        dimensions=["target_name", "tablespace_name"],
        metrics=["used_mb", "allocated_mb", "used_pct"]
    ),
    
    QueryConfig(
        name="cpu_usage_daily",
        sql="""
SELECT
  target_name,
  host_name,
  TO_CHAR(rollup_timestamp, 'YYYY-MM-DD') as rollup_date,
  ROUND(AVG(average), 2) as cpu_avg,
  ROUND(MAX(maximum), 2) as cpu_max
FROM
  sysman.mgmt$metric_daily met
  JOIN sysman.mgmt$target tgt ON (met.target_guid = tgt.target_guid)
WHERE
  tgt.target_type = 'oracle_database'
  AND met.metric_name = 'instance_efficiency'
  AND met.metric_column = 'cpuusage_ps'
  AND met.rollup_timestamp >= SYSDATE - 7
GROUP BY target_name, host_name, TO_CHAR(rollup_timestamp, 'YYYY-MM-DD')
ORDER BY rollup_date, target_name
        """,
        interval=86400,  # Daily
        metric_prefix="oem.db",
        dimensions=["target_name", "host_name", "rollup_date"],
        metrics=["cpu_avg", "cpu_max"]
    ),
    
    QueryConfig(
        name="host_info",
        sql="""
SELECT
  host_name,
  mem as memory_mb,
  cpu_count,
  physical_cpu_count as cpu_sockets,
  total_cpu_cores as cpu_cores,
  logical_cpu_count as cpu_threads,
  virtual
FROM
  sysman.mgmt$os_hw_summary
ORDER BY host_name
        """,
        interval=86400,  # Daily
        metric_prefix="oem.host",
        dimensions=["host_name"],
        metrics=["memory_mb", "cpu_count", "cpu_sockets", "cpu_cores", "cpu_threads"]
    )
]


# =============================================================================
# OEM Repository Collector
# =============================================================================

class OEMRepositoryCollector:
    """
    Collects metrics from OEM Repository database.
    """
    
    def __init__(self, config: CollectorConfig):
        self.config = config
        self.connection = None
        self._oracledb = None
    
    def _get_oracledb(self):
        """Lazy import oracledb"""
        if self._oracledb is None:
            try:
                import oracledb
                self._oracledb = oracledb
            except ImportError:
                try:
                    import cx_Oracle as oracledb
                    self._oracledb = oracledb
                except ImportError:
                    raise ImportError("Neither oracledb nor cx_Oracle installed")
        return self._oracledb
    
    def connect(self) -> bool:
        """Connect to OEM Repository database"""
        try:
            oracledb = self._get_oracledb()
            
            dsn = f"{self.config.oem_repository.host}:{self.config.oem_repository.port}/{self.config.oem_repository.service_name}"
            
            self.connection = oracledb.connect(
                user=self.config.oem_repository.username,
                password=self.config.oem_repository.password,
                dsn=dsn
            )
            
            logger.info(f"✅ Connected to OEM Repository: {dsn}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to OEM Repository: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None
    
    def execute_query(self, query: QueryConfig) -> List[Dict]:
        """Execute a query and return results as list of dicts"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query.sql)
            
            columns = [col[0].lower() for col in cursor.description]
            results = []
            
            for row in cursor:
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            
            logger.debug(f"Query '{query.name}' returned {len(results)} rows")
            return results
            
        except Exception as e:
            logger.error(f"Query '{query.name}' failed: {e}")
            return []
    
    def results_to_metrics(self, query: QueryConfig, results: List[Dict]) -> List[Tuple[str, float, int]]:
        """Convert query results to Graphite metrics"""
        metrics = []
        now = int(time.time())
        
        for row in results:
            # Build dimension path from dimension columns
            dim_parts = []
            for dim in query.dimensions:
                if dim in row and row[dim]:
                    # Sanitize dimension value for metric name
                    safe_val = str(row[dim]).lower()
                    safe_val = re.sub(r'[^a-zA-Z0-9_]', '_', safe_val)
                    dim_parts.append(safe_val)
            
            dim_path = ".".join(dim_parts) if dim_parts else "unknown"
            
            # Create metrics from metric columns
            for metric_col in query.metrics:
                if metric_col in row and row[metric_col] is not None:
                    try:
                        value = float(row[metric_col])
                        metric_name = f"{query.metric_prefix}.{dim_path}.{metric_col}"
                        metrics.append((metric_name, value, now))
                    except (ValueError, TypeError):
                        pass
        
        return metrics
    
    def collect_metrics(self, queries: Optional[List[QueryConfig]] = None) -> List[Tuple[str, float, int]]:
        """Collect metrics from all configured queries"""
        all_metrics = []
        
        if queries is None:
            queries = self.config.queries if self.config.queries else BUILTIN_QUERIES
        
        for query in queries:
            if not query.enabled:
                continue
            
            logger.info(f"📊 Executing query: {query.name}")
            results = self.execute_query(query)
            
            if results:
                metrics = self.results_to_metrics(query, results)
                all_metrics.extend(metrics)
                logger.info(f"  → Collected {len(metrics)} metrics from '{query.name}'")
            else:
                logger.warning(f"  → No results from '{query.name}'")
        
        return all_metrics
    
    def send_to_graphite(self, metrics: List[Tuple[str, float, int]]) -> bool:
        """Send metrics to VictoriaMetrics via Graphite"""
        if not metrics:
            return True
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.config.graphite_host, self.config.graphite_port))
            
            lines = [f"{m[0]} {m[1]} {m[2]}" for m in metrics]
            message = "\n".join(lines) + "\n"
            
            sock.sendall(message.encode())
            sock.close()
            
            logger.info(f"📤 Sent {len(metrics)} metrics to VictoriaMetrics")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send to Graphite: {e}")
            return False
    
    def save_to_mongodb(self, query_name: str, results: List[Dict]):
        """Save raw results to MongoDB for history"""
        if not self.config.mongo_uri:
            return
        
        try:
            from pymongo import MongoClient
            client = MongoClient(self.config.mongo_uri)
            db = client[self.config.mongo_db]
            
            doc = {
                "query_name": query_name,
                "collected_at": datetime.utcnow(),
                "results": results,
                "result_count": len(results)
            }
            
            db.oem_metrics_history.insert_one(doc)
            
            logger.debug(f"Saved {len(results)} results to MongoDB")
            client.close()
            
        except Exception as e:
            logger.warning(f"Failed to save to MongoDB: {e}")
    
    def run_once(self) -> Dict:
        """Run a single collection cycle"""
        logger.info("🚀 Starting OEM Repository collection...")
        
        if not self.connect():
            return {"success": False, "error": "Connection failed"}
        
        try:
            all_metrics = self.collect_metrics()
            
            if all_metrics:
                self.send_to_graphite(all_metrics)
            
            summary = {
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
                "metrics_collected": len(all_metrics),
                "queries_executed": len(self.config.queries) if self.config.queries else len(BUILTIN_QUERIES)
            }
            
            logger.info(f"✅ Collection complete: {len(all_metrics)} metrics")
            return summary
            
        finally:
            self.disconnect()
    
    def run_forever(self):
        """Run continuous collection loop"""
        logger.info("🚀 OEM Repository Collector starting...")
        logger.info(f"📊 Graphite: {self.config.graphite_host}:{self.config.graphite_port}")
        
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"Collection error: {e}")
            
            interval = self.config.default_interval
            logger.info(f"💤 Sleeping {interval}s...")
            time.sleep(interval)


# =============================================================================
# Configuration Loading
# =============================================================================

def load_config_from_yaml(yaml_path: str) -> CollectorConfig:
    """Load configuration from YAML file"""
    config = CollectorConfig()
    
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # OEM Repository connection
    if 'oem_repository' in data:
        oem = data['oem_repository']
        config.oem_repository = OEMRepositoryConfig(
            host=oem.get('host', 'localhost'),
            port=oem.get('port', 1521),
            service_name=oem.get('service_name', 'EMREP'),
            username=oem.get('username', 'sysman'),
            password=oem.get('password', '')
        )
    
    # Graphite
    config.graphite_host = data.get('graphite_host', 'localhost')
    config.graphite_port = data.get('graphite_port', 2003)
    
    # MongoDB
    config.mongo_uri = data.get('mongo_uri', '')
    config.mongo_db = data.get('mongo_db', 'm-dn_cmdb_v2')
    
    # Queries
    if 'queries' in data:
        for q in data['queries']:
            config.queries.append(QueryConfig(
                name=q.get('name', 'unnamed'),
                sql=q.get('sql', ''),
                interval=q.get('interval', 3600),
                enabled=q.get('enabled', True),
                metric_prefix=q.get('metric_prefix', 'oem'),
                dimensions=q.get('dimensions', []),
                metrics=q.get('metrics', [])
            ))
    
    return config


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="OEM Repository Metrics Collector")
    
    # OEM Repository connection
    parser.add_argument("--oem-host", default="localhost", help="OEM Repository host")
    parser.add_argument("--oem-port", type=int, default=1521, help="OEM Repository port")
    parser.add_argument("--oem-service", default="EMREP", help="OEM Repository service name")
    parser.add_argument("--oem-user", default="sysman", help="OEM Repository username")
    parser.add_argument("--oem-pass", default="", help="OEM Repository password")
    
    # Config file
    parser.add_argument("--config", help="Path to YAML config file")
    
    # Output
    parser.add_argument("--graphite-host", default="localhost", help="Graphite/VictoriaMetrics host")
    parser.add_argument("--graphite-port", type=int, default=2003, help="Graphite port")
    
    # Execution
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=3600, help="Collection interval in seconds")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load config
    if args.config and os.path.exists(args.config):
        config = load_config_from_yaml(args.config)
    else:
        config = CollectorConfig()
    
    # Override with CLI args
    config.oem_repository.host = args.oem_host
    config.oem_repository.port = args.oem_port
    config.oem_repository.service_name = args.oem_service
    config.oem_repository.username = args.oem_user
    config.oem_repository.password = args.oem_pass or os.getenv("OEM_PASSWORD", "")
    
    config.graphite_host = args.graphite_host
    config.graphite_port = args.graphite_port
    config.default_interval = args.interval
    
    # Use builtin queries if none configured
    if not config.queries:
        config.queries = BUILTIN_QUERIES
    
    # Run
    collector = OEMRepositoryCollector(config)
    
    if args.once:
        result = collector.run_once()
        print(json.dumps(result, indent=2))
    else:
        collector.run_forever()


if __name__ == "__main__":
    main()
