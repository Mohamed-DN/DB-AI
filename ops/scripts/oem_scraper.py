"""
Oracle Enterprise Manager (OEM) Scraper
========================================
Collects metrics from Oracle Enterprise Manager and Oracle databases directly.

This scraper supports multiple collection methods:
1. OEM REST API (Enterprise Manager 12c/13c Cloud Control)
2. Direct Oracle database queries (via cx_Oracle/oracledb)
3. OEM CLI (emcli) for legacy systems

Architecture:
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│  Oracle DB / OEM    │     │  OEM Scraper        │     │  VictoriaMetrics    │
│  (various sources)  │────▶│  (this script)      │────▶│  (Graphite :2003)   │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘

Usage:
    # Direct Oracle connection
    python oem_scraper.py --oracle-host 10.0.1.10 --oracle-sid ORCL --once
    
    # OEM REST API
    python oem_scraper.py --oem-url https://em.nexi.local:7803/em --once
    
    # From MongoDB inventory
    python oem_scraper.py --discover-from-mongo
"""
import os
import socket
import time
import re
import json
import logging
import argparse
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3

# Disable SSL warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("OEMScraper")


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class OracleTarget:
    """A single Oracle database to scrape"""
    host: str
    port: int = 1521
    service_name: str = ""
    sid: str = ""
    username: str = "nexi_monitor"
    password: str = ""
    name: str = ""  # Friendly name
    datacenter: str = "unknown"
    role: str = "PRIMARY"  # PRIMARY, STANDBY, REPLICA
    timeout: int = 30
    enabled: bool = True
    
    def __post_init__(self):
        if not self.name:
            self.name = self.sid or self.service_name or self.host
    
    @property
    def dsn(self) -> str:
        """Build Oracle DSN"""
        if self.service_name:
            return f"{self.host}:{self.port}/{self.service_name}"
        return f"{self.host}:{self.port}/{self.sid}"


@dataclass
class OEMServerConfig:
    """Oracle Enterprise Manager server configuration"""
    url: str  # https://em.nexi.local:7803/em
    username: str = "sysman"
    password: str = ""
    verify_ssl: bool = False
    timeout: int = 30


@dataclass
class OEMScraperConfig:
    """Main scraper configuration"""
    # Oracle targets (direct connection)
    oracle_targets: List[OracleTarget] = field(default_factory=list)
    
    # OEM servers (REST API)
    oem_servers: List[OEMServerConfig] = field(default_factory=list)
    
    # VictoriaMetrics/Graphite
    graphite_host: str = "localhost"
    graphite_port: int = 2003
    
    # MongoDB for discovery
    mongo_uri: str = "mongodb://admin:nexi2024@localhost:28017/"
    mongo_db: str = "nexi_cmdb_v2"
    discover_from_mongo: bool = True
    
    # Scraping settings
    scrape_interval: int = 60
    max_workers: int = 10


# =============================================================================
# Oracle Direct Metrics Collector
# =============================================================================

class OracleDirectCollector:
    """
    Collects metrics directly from Oracle databases via SQL queries.
    Uses oracledb (python-oracledb) or cx_Oracle.
    """
    
    # Key metrics queries
    METRICS_QUERIES = {
        "instance_status": """
            SELECT INSTANCE_NAME, STATUS, DATABASE_STATUS, 
                   ACTIVE_STATE, BLOCKED, STARTUP_TIME
            FROM V$INSTANCE
        """,
        
        "database_info": """
            SELECT NAME, DB_UNIQUE_NAME, DATABASE_ROLE, OPEN_MODE,
                   PROTECTION_MODE, FORCE_LOGGING, LOG_MODE
            FROM V$DATABASE
        """,
        
        "tablespace_usage": """
            SELECT df.tablespace_name,
                   ROUND(SUM(df.bytes) / 1024 / 1024, 2) as size_mb,
                   ROUND(SUM(df.bytes - NVL(fs.bytes, 0)) / 1024 / 1024, 2) as used_mb,
                   ROUND((SUM(df.bytes - NVL(fs.bytes, 0)) / SUM(df.bytes)) * 100, 2) as used_pct
            FROM (
                SELECT tablespace_name, SUM(bytes) bytes
                FROM dba_data_files
                GROUP BY tablespace_name
            ) df
            LEFT JOIN (
                SELECT tablespace_name, SUM(bytes) bytes
                FROM dba_free_space
                GROUP BY tablespace_name
            ) fs ON df.tablespace_name = fs.tablespace_name
            GROUP BY df.tablespace_name
        """,
        
        "session_stats": """
            SELECT COUNT(*) as total_sessions,
                   SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) as active_sessions,
                   SUM(CASE WHEN status = 'INACTIVE' THEN 1 ELSE 0 END) as inactive_sessions,
                   SUM(CASE WHEN blocking_session IS NOT NULL THEN 1 ELSE 0 END) as blocked_sessions
            FROM V$SESSION
            WHERE type = 'USER'
        """,
        
        "wait_class_stats": """
            SELECT wait_class, 
                   ROUND(SUM(time_waited_micro) / 1000000, 2) as time_waited_seconds,
                   SUM(total_waits) as total_waits
            FROM V$SYSTEM_WAIT_CLASS
            WHERE wait_class != 'Idle'
            GROUP BY wait_class
        """,
        
        "sga_stats": """
            SELECT pool, 
                   ROUND(SUM(bytes) / 1024 / 1024, 2) as size_mb
            FROM V$SGASTAT
            WHERE pool IS NOT NULL
            GROUP BY pool
        """,
        
        "pga_stats": """
            SELECT name, value
            FROM V$PGASTAT
            WHERE name IN ('total PGA allocated', 'total PGA used for auto workareas',
                          'maximum PGA allocated', 'cache hit percentage')
        """,
        
        "redo_stats": """
            SELECT a.member as redo_log,
                   b.bytes / 1024 / 1024 as size_mb,
                   b.status
            FROM V$LOGFILE a
            JOIN V$LOG b ON a.group# = b.group#
        """,
        
        "dataguard_status": """
            SELECT DEST_ID, DEST_NAME, STATUS, ERROR, 
                   APPLIED_SCN, APPLIED_TIME
            FROM V$ARCHIVE_DEST_STATUS
            WHERE TYPE = 'PHYSICAL'
        """,
        
        "asm_diskgroup": """
            SELECT name, state, type, 
                   ROUND(total_mb, 2) as total_mb,
                   ROUND(free_mb, 2) as free_mb,
                   ROUND((1 - free_mb/total_mb) * 100, 2) as used_pct
            FROM V$ASM_DISKGROUP
        """,
        
        "performance_stats": """
            SELECT name, value
            FROM V$SYSSTAT
            WHERE name IN (
                'user commits', 'user rollbacks', 
                'physical reads', 'physical writes',
                'redo writes', 'redo size',
                'parse count (total)', 'parse count (hard)',
                'execute count', 'sorts (memory)', 'sorts (disk)',
                'table scans (long tables)', 'table fetch by rowid'
            )
        """
    }
    
    def __init__(self, target: OracleTarget):
        self.target = target
        self.connection = None
        self._oracledb = None
    
    def _get_oracledb(self):
        """Get oracledb module (lazy import)"""
        if self._oracledb is None:
            try:
                import oracledb
                self._oracledb = oracledb
            except ImportError:
                try:
                    import cx_Oracle as oracledb
                    self._oracledb = oracledb
                except ImportError:
                    raise ImportError("Neither oracledb nor cx_Oracle is installed")
        return self._oracledb
    
    def connect(self) -> bool:
        """Connect to Oracle database"""
        try:
            oracledb = self._get_oracledb()
            
            self.connection = oracledb.connect(
                user=self.target.username,
                password=self.target.password,
                dsn=self.target.dsn
            )
            
            logger.debug(f"Connected to {self.target.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.target.name}: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Oracle database"""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None
    
    def execute_query(self, query: str) -> List[Dict]:
        """Execute a query and return results as list of dicts"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            columns = [col[0].lower() for col in cursor.description]
            results = []
            
            for row in cursor:
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            return results
            
        except Exception as e:
            logger.debug(f"Query failed: {e}")
            return []
    
    def collect_metrics(self) -> List[Tuple[str, float, int]]:
        """Collect all metrics from Oracle database"""
        metrics = []
        now = int(time.time())
        prefix = f"oracle.{self.target.name}"
        
        if not self.connect():
            # Return connection failure metric
            metrics.append((f"{prefix}.connection.status", 0, now))
            return metrics
        
        metrics.append((f"{prefix}.connection.status", 1, now))
        
        try:
            # Instance status
            results = self.execute_query(self.METRICS_QUERIES["instance_status"])
            if results:
                row = results[0]
                status = 1 if row.get('status') == 'OPEN' else 0
                metrics.append((f"{prefix}.instance.status", status, now))
                metrics.append((f"{prefix}.instance.active", 
                              1 if row.get('active_state') == 'NORMAL' else 0, now))
            
            # Database info
            results = self.execute_query(self.METRICS_QUERIES["database_info"])
            if results:
                row = results[0]
                role = 1 if row.get('database_role') == 'PRIMARY' else 0
                metrics.append((f"{prefix}.database.is_primary", role, now))
                open_mode = 1 if row.get('open_mode') == 'READ WRITE' else 0
                metrics.append((f"{prefix}.database.is_readwrite", open_mode, now))
            
            # Tablespace usage
            for row in self.execute_query(self.METRICS_QUERIES["tablespace_usage"]):
                ts_name = row.get('tablespace_name', 'unknown')
                safe_ts = re.sub(r'[^a-zA-Z0-9_]', '_', ts_name)
                metrics.append((f"{prefix}.tablespace.{safe_ts}.size_mb", 
                              float(row.get('size_mb', 0)), now))
                metrics.append((f"{prefix}.tablespace.{safe_ts}.used_mb", 
                              float(row.get('used_mb', 0)), now))
                metrics.append((f"{prefix}.tablespace.{safe_ts}.used_pct", 
                              float(row.get('used_pct', 0)), now))
            
            # Session stats
            results = self.execute_query(self.METRICS_QUERIES["session_stats"])
            if results:
                row = results[0]
                metrics.append((f"{prefix}.sessions.total", int(row.get('total_sessions', 0)), now))
                metrics.append((f"{prefix}.sessions.active", int(row.get('active_sessions', 0)), now))
                metrics.append((f"{prefix}.sessions.inactive", int(row.get('inactive_sessions', 0)), now))
                metrics.append((f"{prefix}.sessions.blocked", int(row.get('blocked_sessions', 0)), now))
            
            # Wait class stats
            for row in self.execute_query(self.METRICS_QUERIES["wait_class_stats"]):
                wait_class = row.get('wait_class', 'unknown')
                safe_wc = re.sub(r'[^a-zA-Z0-9_]', '_', wait_class.lower())
                metrics.append((f"{prefix}.waits.{safe_wc}.time_seconds", 
                              float(row.get('time_waited_seconds', 0)), now))
                metrics.append((f"{prefix}.waits.{safe_wc}.count", 
                              int(row.get('total_waits', 0)), now))
            
            # SGA stats
            for row in self.execute_query(self.METRICS_QUERIES["sga_stats"]):
                pool = row.get('pool', 'unknown')
                safe_pool = re.sub(r'[^a-zA-Z0-9_]', '_', pool.lower())
                metrics.append((f"{prefix}.sga.{safe_pool}_mb", 
                              float(row.get('size_mb', 0)), now))
            
            # Performance stats
            for row in self.execute_query(self.METRICS_QUERIES["performance_stats"]):
                stat_name = row.get('name', 'unknown')
                safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', stat_name.lower())
                safe_name = safe_name.replace('__', '_')
                metrics.append((f"{prefix}.stats.{safe_name}", 
                              float(row.get('value', 0)), now))
            
            # ASM diskgroups (if applicable)
            for row in self.execute_query(self.METRICS_QUERIES["asm_diskgroup"]):
                dg_name = row.get('name', 'unknown')
                safe_dg = re.sub(r'[^a-zA-Z0-9_]', '_', dg_name)
                metrics.append((f"{prefix}.asm.{safe_dg}.total_mb", 
                              float(row.get('total_mb', 0)), now))
                metrics.append((f"{prefix}.asm.{safe_dg}.free_mb", 
                              float(row.get('free_mb', 0)), now))
                metrics.append((f"{prefix}.asm.{safe_dg}.used_pct", 
                              float(row.get('used_pct', 0)), now))
            
            # Data Guard status
            for row in self.execute_query(self.METRICS_QUERIES["dataguard_status"]):
                dest_name = row.get('dest_name', 'unknown')
                safe_dest = re.sub(r'[^a-zA-Z0-9_]', '_', dest_name)
                status_val = 1 if row.get('status') == 'VALID' else 0
                metrics.append((f"{prefix}.dataguard.{safe_dest}.status", status_val, now))
            
        finally:
            self.disconnect()
        
        logger.info(f"  📊 Collected {len(metrics)} metrics from {self.target.name}")
        return metrics


# =============================================================================
# OEM REST API Collector
# =============================================================================

class OEMRestCollector:
    """
    Collects metrics from Oracle Enterprise Manager via REST API.
    Supports OEM 12c/13c Cloud Control.
    """
    
    def __init__(self, config: OEMServerConfig):
        self.config = config
        self.base_url = config.url.rstrip('/')
        self.session = None
    
    def _get_session(self):
        """Get or create HTTP session"""
        if self.session is None:
            import requests
            self.session = requests.Session()
            self.session.auth = (self.config.username, self.config.password)
            self.session.verify = self.config.verify_ssl
            self.session.headers.update({
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            })
        return self.session
    
    def get_targets(self) -> List[Dict]:
        """Get all database targets from OEM"""
        try:
            session = self._get_session()
            url = f"{self.base_url}/api/targets"
            
            resp = session.get(url, timeout=self.config.timeout)
            
            if resp.status_code == 200:
                data = resp.json()
                # Filter for database targets
                db_targets = [
                    t for t in data.get('items', [])
                    if t.get('targetType') in ['oracle_database', 'rac_database', 'oracle_pdb']
                ]
                logger.info(f"Found {len(db_targets)} database targets in OEM")
                return db_targets
            else:
                logger.error(f"OEM API returned {resp.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get OEM targets: {e}")
            return []
    
    def get_target_metrics(self, target_name: str, target_type: str = "oracle_database") -> List[Dict]:
        """Get metrics for a specific target"""
        try:
            session = self._get_session()
            
            # Get real-time metrics
            url = f"{self.base_url}/api/targets/{target_type}/{target_name}/metrics"
            
            resp = session.get(url, timeout=self.config.timeout)
            
            if resp.status_code == 200:
                return resp.json().get('items', [])
            return []
            
        except Exception as e:
            logger.error(f"Failed to get metrics for {target_name}: {e}")
            return []
    
    def get_incidents(self) -> List[Dict]:
        """Get current incidents/alerts from OEM"""
        try:
            session = self._get_session()
            url = f"{self.base_url}/api/incidents"
            
            resp = session.get(url, params={'status': 'open'}, timeout=self.config.timeout)
            
            if resp.status_code == 200:
                incidents = resp.json().get('items', [])
                logger.info(f"Found {len(incidents)} open incidents in OEM")
                return incidents
            return []
            
        except Exception as e:
            logger.error(f"Failed to get OEM incidents: {e}")
            return []
    
    def collect_all_metrics(self) -> List[Tuple[str, float, int]]:
        """Collect metrics from all database targets in OEM"""
        metrics = []
        now = int(time.time())
        
        targets = self.get_targets()
        
        for target in targets:
            target_name = target.get('targetName', 'unknown')
            target_type = target.get('targetType', 'oracle_database')
            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', target_name)
            prefix = f"oem.{safe_name}"
            
            # Target status
            status = 1 if target.get('availability', {}).get('status') == 'UP' else 0
            metrics.append((f"{prefix}.status", status, now))
            
            # Get detailed metrics
            target_metrics = self.get_target_metrics(target_name, target_type)
            for m in target_metrics:
                metric_name = m.get('name', 'unknown')
                value = m.get('value')
                if value is not None:
                    try:
                        safe_metric = re.sub(r'[^a-zA-Z0-9_]', '_', metric_name.lower())
                        metrics.append((f"{prefix}.{safe_metric}", float(value), now))
                    except (ValueError, TypeError):
                        pass
        
        # Incidents count
        incidents = self.get_incidents()
        metrics.append(("oem.incidents.open_count", len(incidents), now))
        
        # Count by severity
        severity_counts = {}
        for inc in incidents:
            sev = inc.get('severity', 'unknown')
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        for sev, count in severity_counts.items():
            safe_sev = re.sub(r'[^a-zA-Z0-9_]', '_', sev.lower())
            metrics.append((f"oem.incidents.{safe_sev}", count, now))
        
        return metrics


# =============================================================================
# Main OEM Scraper
# =============================================================================

class OEMScraper:
    """Main Oracle Enterprise Manager / Oracle database scraper"""
    
    def __init__(self, config: OEMScraperConfig):
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
    
    def scrape_oracle_target(self, target: OracleTarget) -> Dict:
        """Scrape a single Oracle database"""
        if not target.enabled:
            return {"target": target.name, "success": False, "reason": "disabled"}
        
        logger.info(f"📡 Scraping Oracle: {target.name} ({target.dsn})")
        
        start_time = time.time()
        collector = OracleDirectCollector(target)
        metrics = collector.collect_metrics()
        duration = time.time() - start_time
        
        return {
            "target": target.name,
            "success": len(metrics) > 0,
            "metrics": metrics,
            "duration": duration
        }
    
    def scrape_oem_server(self, oem_config: OEMServerConfig) -> Dict:
        """Scrape an OEM server via REST API"""
        logger.info(f"📡 Scraping OEM: {oem_config.url}")
        
        start_time = time.time()
        collector = OEMRestCollector(oem_config)
        metrics = collector.collect_all_metrics()
        duration = time.time() - start_time
        
        return {
            "oem_url": oem_config.url,
            "success": len(metrics) > 0,
            "metrics": metrics,
            "duration": duration
        }
    
    def scrape_all(self) -> List[Dict]:
        """Scrape all targets"""
        results = []
        
        # Scrape Oracle databases directly
        futures = {}
        for target in self.config.oracle_targets:
            future = self.executor.submit(self.scrape_oracle_target, target)
            futures[future] = target
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                target = futures[future]
                logger.error(f"Exception scraping {target.name}: {e}")
                results.append({"target": target.name, "success": False, "reason": str(e)})
        
        # Scrape OEM servers
        for oem_config in self.config.oem_servers:
            try:
                result = self.scrape_oem_server(oem_config)
                results.append(result)
            except Exception as e:
                logger.error(f"Exception scraping OEM {oem_config.url}: {e}")
        
        return results
    
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
            
            logger.debug(f"📊 Sent {len(metrics)} Oracle metrics to Graphite")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send to Graphite: {e}")
            return False
    
    def run_once(self) -> Dict:
        """Run single scrape cycle"""
        logger.info(f"Starting Oracle scrape: {len(self.config.oracle_targets)} DBs, {len(self.config.oem_servers)} OEM servers")
        
        results = self.scrape_all()
        
        # Aggregate metrics
        all_metrics = []
        for result in results:
            all_metrics.extend(result.get("metrics", []))
        
        # Send to VictoriaMetrics
        if all_metrics:
            self.send_to_graphite(all_metrics)
        
        success_count = sum(1 for r in results if r.get("success"))
        
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "targets_total": len(self.config.oracle_targets) + len(self.config.oem_servers),
            "targets_success": success_count,
            "metrics_collected": len(all_metrics)
        }
        
        logger.info(f"✅ Oracle scrape complete: {len(all_metrics)} metrics")
        return summary
    
    def run_forever(self):
        """Run continuous scrape loop"""
        logger.info("🚀 OEM Scraper starting...")
        
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"Scrape cycle error: {e}")
            
            logger.info(f"💤 Sleeping {self.config.scrape_interval}s...")
            time.sleep(self.config.scrape_interval)


# =============================================================================
# Discovery from MongoDB
# =============================================================================

def discover_oracle_from_mongo(mongo_uri: str, mongo_db: str) -> List[OracleTarget]:
    """Discover Oracle targets from MongoDB inventory"""
    targets = []
    
    try:
        from pymongo import MongoClient
        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        
        # Get Oracle databases
        databases = list(db.inventory_databases.find({
            "identity.type": {"$in": ["ORACLE", "oracle"]},
            "status": {"$ne": "deleted"}
        }))
        
        logger.info(f"📋 Found {len(databases)} Oracle databases in MongoDB")
        
        for db_doc in databases:
            identity = db_doc.get("identity", {})
            host = identity.get("host", "")
            sid = identity.get("sid", "")
            service_name = identity.get("service_name", "")
            db_name = identity.get("db_unique_name", "")
            port = identity.get("port", 1521)
            datacenter = db_doc.get("datacenter", "unknown")
            
            # Get credentials from connection info
            conn_info = db_doc.get("connection_info", {})
            username = conn_info.get("monitoring_user", "nexi_monitor")
            password = conn_info.get("monitoring_password", "")
            
            if host and (sid or service_name):
                targets.append(OracleTarget(
                    host=host,
                    port=port,
                    sid=sid,
                    service_name=service_name,
                    username=username,
                    password=password,
                    name=db_name or sid or service_name,
                    datacenter=datacenter,
                    enabled=True
                ))
        
        client.close()
        
    except Exception as e:
        logger.error(f"Error discovering from MongoDB: {e}")
    
    return targets


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Oracle Enterprise Manager Scraper")
    
    # Oracle direct connection
    parser.add_argument("--oracle-host", help="Oracle database host")
    parser.add_argument("--oracle-port", type=int, default=1521, help="Oracle port")
    parser.add_argument("--oracle-sid", help="Oracle SID")
    parser.add_argument("--oracle-service", help="Oracle service name")
    parser.add_argument("--oracle-user", default="nexi_monitor", help="Oracle username")
    parser.add_argument("--oracle-pass", default="", help="Oracle password")
    
    # OEM REST API
    parser.add_argument("--oem-url", help="OEM base URL (e.g., https://em:7803/em)")
    parser.add_argument("--oem-user", default="sysman", help="OEM username")
    parser.add_argument("--oem-pass", default="", help="OEM password")
    
    # General
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=60, help="Scrape interval")
    parser.add_argument("--graphite-host", default="localhost", help="Graphite host")
    parser.add_argument("--graphite-port", type=int, default=2003, help="Graphite port")
    parser.add_argument("--mongo-uri", help="MongoDB URI for discovery")
    parser.add_argument("--discover-from-mongo", action="store_true", help="Discover from MongoDB")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Build config
    config = OEMScraperConfig(
        graphite_host=args.graphite_host,
        graphite_port=args.graphite_port,
        scrape_interval=args.interval
    )
    
    # Add Oracle target if specified
    if args.oracle_host:
        config.oracle_targets.append(OracleTarget(
            host=args.oracle_host,
            port=args.oracle_port,
            sid=args.oracle_sid or "",
            service_name=args.oracle_service or "",
            username=args.oracle_user,
            password=args.oracle_pass
        ))
    
    # Add OEM server if specified
    if args.oem_url:
        config.oem_servers.append(OEMServerConfig(
            url=args.oem_url,
            username=args.oem_user,
            password=args.oem_pass
        ))
    
    # Discover from MongoDB
    if args.discover_from_mongo or args.mongo_uri:
        mongo_uri = args.mongo_uri or os.getenv("MONGO_URI", "mongodb://admin:nexi2024@localhost:28017/")
        config.oracle_targets.extend(discover_oracle_from_mongo(mongo_uri, "nexi_cmdb_v2"))
    
    if not config.oracle_targets and not config.oem_servers:
        logger.error("No targets found! Use --oracle-host, --oem-url, or --discover-from-mongo")
        return
    
    # Run
    scraper = OEMScraper(config)
    
    if args.once:
        result = scraper.run_once()
        print(json.dumps(result, indent=2))
    else:
        scraper.run_forever()


if __name__ == "__main__":
    main()
