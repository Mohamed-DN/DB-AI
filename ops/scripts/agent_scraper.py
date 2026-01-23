"""
CheckMK Agent Scraper - Direct Agent Collection
================================================
Collects metrics directly from CheckMK agents on port 6556.
This is a PASSIVE approach - we only READ data, never modify anything.

Architecture:
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│  DB Server          │     │  Agent Scraper      │     │  VictoriaMetrics    │
│  Agent :6556        │────▶│  (this script)      │────▶│  (Graphite :2003)   │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘

The CheckMK agent 1.5.x listens on port 6556 and outputs its data when
a TCP connection is made. We simply connect, read, parse, and forward metrics.

Usage:
    python agent_scraper.py --config agents.yaml
    python agent_scraper.py --host 10.0.1.10 --port 6556 --once
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AgentScraper")


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class AgentTarget:
    """A single agent to scrape"""
    host: str
    port: int = 6556
    name: str = ""  # Friendly name, defaults to host
    datacenter: str = "unknown"
    db_type: str = "unknown"  # POSTGRES, ORACLE, MONGODB, etc.
    timeout: int = 30
    enabled: bool = True
    
    def __post_init__(self):
        if not self.name:
            self.name = self.host


@dataclass
class ScraperConfig:
    """Main scraper configuration"""
    targets: List[AgentTarget] = field(default_factory=list)
    
    # VictoriaMetrics/Graphite
    graphite_host: str = "localhost"
    graphite_port: int = 2003
    
    # MongoDB for target discovery
    mongo_uri: str = "mongodb://admin:nexi2024@localhost:28017/"
    mongo_db: str = "nexi_cmdb_v2"
    discover_from_mongo: bool = True
    
    # Scraping settings
    scrape_interval: int = 60
    max_workers: int = 10
    timeout: int = 30


# =============================================================================
# Agent Output Parser
# =============================================================================

class CheckMKAgentParser:
    """
    Parser for CheckMK agent output (1.5.x format).
    
    The agent output consists of sections marked by <<<section_name>>>.
    Each section contains check-specific data.
    """
    
    # Regex patterns
    SECTION_PATTERN = re.compile(r'<<<([^>]+)>>>')
    
    def __init__(self, raw_output: str, hostname: str = "unknown"):
        self.raw_output = raw_output
        self.hostname = hostname
        self.sections: Dict[str, List[str]] = {}
        self._parse_sections()
    
    def _parse_sections(self):
        """Parse raw output into sections"""
        current_section = "header"
        self.sections[current_section] = []
        
        for line in self.raw_output.split('\n'):
            match = self.SECTION_PATTERN.match(line.strip())
            if match:
                current_section = match.group(1)
                # Handle section options like <<<local:sep(0)>>>
                if ':' in current_section:
                    current_section = current_section.split(':')[0]
                self.sections[current_section] = []
            else:
                if line.strip():
                    self.sections.setdefault(current_section, []).append(line)
    
    def get_section(self, name: str) -> List[str]:
        """Get lines from a specific section"""
        return self.sections.get(name, [])
    
    def list_sections(self) -> List[str]:
        """List all available sections"""
        return list(self.sections.keys())
    
    def extract_metrics(self) -> List[Tuple[str, float, int]]:
        """
        Extract all metrics in Graphite format.
        Returns: List of (metric_name, value, timestamp)
        """
        metrics = []
        now = int(time.time())
        prefix = f"checkmk.agent.{self.hostname}"
        
        # CPU metrics (from <<<cpu>>> section)
        metrics.extend(self._parse_cpu(prefix, now))
        
        # Memory metrics (from <<<mem>>> section)
        metrics.extend(self._parse_memory(prefix, now))
        
        # Disk metrics (from <<<df>>> section)
        metrics.extend(self._parse_disk(prefix, now))
        
        # Uptime (from <<<uptime>>> section)
        metrics.extend(self._parse_uptime(prefix, now))
        
        # TCP connections (from <<<tcp_conn_stats>>> section)
        metrics.extend(self._parse_tcp_connections(prefix, now))
        
        # Kernel stats (from <<<kernel>>> section)
        metrics.extend(self._parse_kernel(prefix, now))
        
        # Local check results (from <<<local>>> section)
        metrics.extend(self._parse_local_checks(prefix, now))
        
        # Oracle specific (from <<<oracle_*>>> sections)
        metrics.extend(self._parse_oracle(prefix, now))
        
        # PostgreSQL specific (from <<<postgres_*>>> sections)
        metrics.extend(self._parse_postgres(prefix, now))
        
        return metrics
    
    def _parse_cpu(self, prefix: str, ts: int) -> List[Tuple[str, float, int]]:
        """Parse <<<cpu>>> section"""
        metrics = []
        lines = self.get_section("cpu")
        
        if lines:
            # Format: load1 load5 load15 running/total last_pid
            parts = lines[0].split()
            if len(parts) >= 3:
                try:
                    metrics.append((f"{prefix}.cpu.load1", float(parts[0]), ts))
                    metrics.append((f"{prefix}.cpu.load5", float(parts[1]), ts))
                    metrics.append((f"{prefix}.cpu.load15", float(parts[2]), ts))
                except (ValueError, IndexError):
                    pass
            
            if len(parts) >= 4 and '/' in parts[3]:
                running, total = parts[3].split('/')
                try:
                    metrics.append((f"{prefix}.cpu.processes_running", int(running), ts))
                    metrics.append((f"{prefix}.cpu.processes_total", int(total), ts))
                except ValueError:
                    pass
        
        return metrics
    
    def _parse_memory(self, prefix: str, ts: int) -> List[Tuple[str, float, int]]:
        """Parse <<<mem>>> section"""
        metrics = []
        mem_data = {}
        
        for line in self.get_section("mem"):
            parts = line.split(':')
            if len(parts) >= 2:
                key = parts[0].strip().lower().replace(' ', '_')
                value = parts[1].strip().split()[0]  # Remove 'kB' suffix
                try:
                    mem_data[key] = int(value)
                except ValueError:
                    pass
        
        # Extract key metrics
        if 'memtotal' in mem_data and 'memfree' in mem_data:
            total = mem_data['memtotal']
            free = mem_data['memfree']
            used = total - free
            usage_pct = (used / total * 100) if total > 0 else 0
            
            metrics.append((f"{prefix}.memory.total_kb", total, ts))
            metrics.append((f"{prefix}.memory.free_kb", free, ts))
            metrics.append((f"{prefix}.memory.used_kb", used, ts))
            metrics.append((f"{prefix}.memory.usage_percent", round(usage_pct, 2), ts))
        
        if 'swaptotal' in mem_data and 'swapfree' in mem_data:
            swap_total = mem_data['swaptotal']
            swap_free = mem_data['swapfree']
            swap_used = swap_total - swap_free
            swap_pct = (swap_used / swap_total * 100) if swap_total > 0 else 0
            
            metrics.append((f"{prefix}.swap.total_kb", swap_total, ts))
            metrics.append((f"{prefix}.swap.used_kb", swap_used, ts))
            metrics.append((f"{prefix}.swap.usage_percent", round(swap_pct, 2), ts))
        
        return metrics
    
    def _parse_disk(self, prefix: str, ts: int) -> List[Tuple[str, float, int]]:
        """Parse <<<df>>> section"""
        metrics = []
        
        for line in self.get_section("df"):
            parts = line.split()
            # Format: filesystem type size used avail percent mount
            if len(parts) >= 6:
                try:
                    filesystem = parts[0]
                    mount = parts[-1].replace('/', '_').strip('_') or 'root'
                    size = int(parts[2]) if parts[2].isdigit() else 0
                    used = int(parts[3]) if parts[3].isdigit() else 0
                    avail = int(parts[4]) if parts[4].isdigit() else 0
                    
                    # Skip virtual filesystems
                    if filesystem.startswith('/dev') or mount in ['tmp', 'var_tmp']:
                        continue
                    
                    usage_pct = (used / size * 100) if size > 0 else 0
                    
                    safe_mount = re.sub(r'[^a-zA-Z0-9_]', '_', mount)
                    metrics.append((f"{prefix}.disk.{safe_mount}.size_kb", size, ts))
                    metrics.append((f"{prefix}.disk.{safe_mount}.used_kb", used, ts))
                    metrics.append((f"{prefix}.disk.{safe_mount}.avail_kb", avail, ts))
                    metrics.append((f"{prefix}.disk.{safe_mount}.usage_percent", round(usage_pct, 2), ts))
                except (ValueError, IndexError):
                    pass
        
        return metrics
    
    def _parse_uptime(self, prefix: str, ts: int) -> List[Tuple[str, float, int]]:
        """Parse <<<uptime>>> section"""
        metrics = []
        lines = self.get_section("uptime")
        
        if lines:
            parts = lines[0].split()
            if parts:
                try:
                    uptime_seconds = float(parts[0])
                    metrics.append((f"{prefix}.uptime_seconds", uptime_seconds, ts))
                    metrics.append((f"{prefix}.uptime_days", round(uptime_seconds / 86400, 2), ts))
                except ValueError:
                    pass
        
        return metrics
    
    def _parse_tcp_connections(self, prefix: str, ts: int) -> List[Tuple[str, float, int]]:
        """Parse <<<tcp_conn_stats>>> section"""
        metrics = []
        
        for line in self.get_section("tcp_conn_stats"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    state = parts[0].lower()
                    count = int(parts[1])
                    metrics.append((f"{prefix}.tcp.{state}", count, ts))
                except (ValueError, IndexError):
                    pass
        
        return metrics
    
    def _parse_kernel(self, prefix: str, ts: int) -> List[Tuple[str, float, int]]:
        """Parse <<<kernel>>> section"""
        metrics = []
        
        for line in self.get_section("kernel"):
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0].lower()
                try:
                    value = float(parts[1])
                    if key in ['processes', 'ctxt', 'procs_running', 'procs_blocked']:
                        metrics.append((f"{prefix}.kernel.{key}", value, ts))
                except (ValueError, IndexError):
                    pass
        
        return metrics
    
    def _parse_local_checks(self, prefix: str, ts: int) -> List[Tuple[str, float, int]]:
        """Parse <<<local>>> section - custom local checks"""
        metrics = []
        
        for line in self.get_section("local"):
            parts = line.split(None, 3)  # status name perf_data output
            if len(parts) >= 2:
                try:
                    status = int(parts[0])  # 0=OK, 1=WARN, 2=CRIT
                    check_name = parts[1].lower().replace(' ', '_')
                    metrics.append((f"{prefix}.local.{check_name}.status", status, ts))
                    
                    # Try to parse performance data
                    if len(parts) >= 3 and '=' in parts[2]:
                        for perf in parts[2].split('|')[0].split():
                            if '=' in perf:
                                pname, pvalue = perf.split('=', 1)
                                # Extract numeric value
                                numeric = re.match(r'([\d.]+)', pvalue)
                                if numeric:
                                    metrics.append((
                                        f"{prefix}.local.{check_name}.{pname}",
                                        float(numeric.group(1)), ts
                                    ))
                except (ValueError, IndexError):
                    pass
        
        return metrics
    
    def _parse_oracle(self, prefix: str, ts: int) -> List[Tuple[str, float, int]]:
        """Parse Oracle-specific sections"""
        metrics = []
        
        # Oracle instance status
        for line in self.get_section("oracle_instance"):
            parts = line.split()
            if len(parts) >= 3:
                sid = parts[0]
                status = 1 if parts[2] == 'OPEN' else 0
                metrics.append((f"{prefix}.oracle.{sid}.status", status, ts))
        
        # Oracle tablespace
        for line in self.get_section("oracle_tablespaces"):
            parts = line.split()
            if len(parts) >= 6:
                sid = parts[0]
                tablespace = parts[1]
                try:
                    used_pct = float(parts[5])
                    safe_ts = re.sub(r'[^a-zA-Z0-9_]', '_', tablespace)
                    metrics.append((f"{prefix}.oracle.{sid}.tablespace.{safe_ts}.used_percent", used_pct, ts))
                except (ValueError, IndexError):
                    pass
        
        # Oracle sessions
        for line in self.get_section("oracle_sessions"):
            parts = line.split()
            if len(parts) >= 3:
                sid = parts[0]
                try:
                    sessions = int(parts[1])
                    metrics.append((f"{prefix}.oracle.{sid}.sessions", sessions, ts))
                except (ValueError, IndexError):
                    pass
        
        return metrics
    
    def _parse_postgres(self, prefix: str, ts: int) -> List[Tuple[str, float, int]]:
        """Parse PostgreSQL-specific sections"""
        metrics = []
        
        # Postgres stats
        for line in self.get_section("postgres_stats"):
            parts = line.split()
            if len(parts) >= 3:
                db = parts[0]
                try:
                    connections = int(parts[1]) if parts[1].isdigit() else 0
                    metrics.append((f"{prefix}.postgres.{db}.connections", connections, ts))
                except (ValueError, IndexError):
                    pass
        
        # Postgres bloat
        for line in self.get_section("postgres_bloat"):
            parts = line.split()
            if len(parts) >= 4:
                db = parts[0]
                table = parts[1]
                try:
                    bloat_pct = float(parts[3])
                    safe_table = re.sub(r'[^a-zA-Z0-9_]', '_', table)
                    metrics.append((f"{prefix}.postgres.{db}.bloat.{safe_table}", bloat_pct, ts))
                except (ValueError, IndexError):
                    pass
        
        return metrics


# =============================================================================
# Agent Scraper
# =============================================================================

class AgentScraper:
    """
    Scrapes CheckMK agents directly on port 6556.
    
    This is a PASSIVE approach - we only read data, never modify anything.
    """
    
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
    
    def _connect_and_read(self, target: AgentTarget) -> Optional[str]:
        """Connect to agent and read output"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(target.timeout)
            sock.connect((target.host, target.port))
            
            # Read all data
            chunks = []
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
            
            sock.close()
            
            output = b''.join(chunks).decode('utf-8', errors='replace')
            logger.debug(f"Received {len(output)} bytes from {target.host}")
            return output
            
        except socket.timeout:
            logger.warning(f"Timeout connecting to {target.host}:{target.port}")
            return None
        except socket.error as e:
            logger.error(f"Socket error for {target.host}:{target.port}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error scraping {target.host}: {e}")
            return None
    
    def scrape_target(self, target: AgentTarget) -> Dict:
        """Scrape a single target and return metrics"""
        if not target.enabled:
            return {"target": target.name, "success": False, "reason": "disabled"}
        
        logger.info(f"📡 Scraping {target.name} ({target.host}:{target.port})")
        
        start_time = time.time()
        raw_output = self._connect_and_read(target)
        scrape_duration = time.time() - start_time
        
        if raw_output is None:
            return {
                "target": target.name,
                "success": False,
                "reason": "connection failed",
                "duration": scrape_duration
            }
        
        # Parse output
        parser = CheckMKAgentParser(raw_output, hostname=target.name)
        metrics = parser.extract_metrics()
        
        # Add scrape metadata
        now = int(time.time())
        prefix = f"checkmk.agent.{target.name}"
        metrics.append((f"{prefix}.scrape.duration_seconds", round(scrape_duration, 3), now))
        metrics.append((f"{prefix}.scrape.success", 1, now))
        metrics.append((f"{prefix}.scrape.sections_count", len(parser.list_sections()), now))
        
        logger.info(f"  ✅ {target.name}: {len(metrics)} metrics, {len(parser.list_sections())} sections")
        
        return {
            "target": target.name,
            "success": True,
            "metrics": metrics,
            "sections": parser.list_sections(),
            "duration": scrape_duration
        }
    
    def scrape_all(self) -> List[Dict]:
        """Scrape all targets in parallel"""
        results = []
        futures = {
            self.executor.submit(self.scrape_target, target): target 
            for target in self.config.targets
        }
        
        for future in as_completed(futures):
            target = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Exception scraping {target.name}: {e}")
                results.append({
                    "target": target.name,
                    "success": False,
                    "reason": str(e)
                })
        
        return results
    
    def send_to_graphite(self, metrics: List[Tuple[str, float, int]]) -> bool:
        """Send metrics to VictoriaMetrics via Graphite protocol"""
        if not metrics:
            return True
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.config.graphite_host, self.config.graphite_port))
            
            # Build message
            lines = [f"{m[0]} {m[1]} {m[2]}" for m in metrics]
            message = "\n".join(lines) + "\n"
            
            sock.sendall(message.encode())
            sock.close()
            
            logger.debug(f"📊 Sent {len(metrics)} metrics to Graphite")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send to Graphite: {e}")
            return False
    
    def run_once(self) -> Dict:
        """Run a single scrape cycle"""
        logger.info(f"Starting scrape cycle for {len(self.config.targets)} targets...")
        
        results = self.scrape_all()
        
        # Aggregate metrics
        all_metrics = []
        success_count = 0
        failed_count = 0
        
        for result in results:
            if result.get("success"):
                success_count += 1
                all_metrics.extend(result.get("metrics", []))
            else:
                failed_count += 1
        
        # Send to Graphite/VictoriaMetrics
        if all_metrics:
            self.send_to_graphite(all_metrics)
        
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "targets_total": len(self.config.targets),
            "targets_success": success_count,
            "targets_failed": failed_count,
            "metrics_collected": len(all_metrics)
        }
        
        logger.info(f"✅ Scrape complete: {success_count}/{len(self.config.targets)} targets, {len(all_metrics)} metrics")
        
        return summary
    
    def run_forever(self):
        """Run continuous scrape loop"""
        logger.info("🚀 Agent Scraper starting...")
        logger.info(f"📡 Targets: {len(self.config.targets)}")
        logger.info(f"📊 Graphite: {self.config.graphite_host}:{self.config.graphite_port}")
        logger.info(f"⏰ Interval: {self.config.scrape_interval}s")
        
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"Scrape cycle error: {e}")
            
            logger.info(f"💤 Sleeping {self.config.scrape_interval}s...")
            time.sleep(self.config.scrape_interval)


# =============================================================================
# Target Discovery from MongoDB
# =============================================================================

def discover_targets_from_mongo(mongo_uri: str, mongo_db: str) -> List[AgentTarget]:
    """Discover agent targets from MongoDB inventory"""
    targets = []
    
    try:
        from pymongo import MongoClient
        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        
        # Get all databases from inventory
        databases = list(db.inventory_databases.find({"status": {"$ne": "deleted"}}))
        
        logger.info(f"📋 Found {len(databases)} databases in MongoDB")
        
        for db_doc in databases:
            identity = db_doc.get("identity", {})
            host = identity.get("host", "")
            db_name = identity.get("db_unique_name", "")
            db_type = identity.get("type", "unknown")
            datacenter = db_doc.get("datacenter", "unknown")
            
            if host:
                targets.append(AgentTarget(
                    host=host,
                    port=6556,
                    name=db_name or host,
                    datacenter=datacenter,
                    db_type=db_type,
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
    parser = argparse.ArgumentParser(description="CheckMK Agent Scraper - Direct Agent Collection")
    parser.add_argument("--host", help="Single host to scrape")
    parser.add_argument("--port", type=int, default=6556, help="Agent port (default: 6556)")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=60, help="Scrape interval in seconds")
    parser.add_argument("--graphite-host", default="localhost", help="Graphite/VictoriaMetrics host")
    parser.add_argument("--graphite-port", type=int, default=2003, help="Graphite port")
    parser.add_argument("--mongo-uri", help="MongoDB URI for target discovery")
    parser.add_argument("--mongo-db", default="nexi_cmdb_v2", help="MongoDB database name")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Build configuration
    config = ScraperConfig(
        graphite_host=args.graphite_host,
        graphite_port=args.graphite_port,
        scrape_interval=args.interval
    )
    
    # Determine targets
    if args.host:
        # Single host mode
        config.targets = [AgentTarget(host=args.host, port=args.port)]
    elif args.mongo_uri:
        # Discover from MongoDB
        config.targets = discover_targets_from_mongo(args.mongo_uri, args.mongo_db)
    else:
        # Try default MongoDB
        mongo_uri = os.getenv("MONGO_URI", "mongodb://admin:nexi2024@localhost:28017/")
        config.targets = discover_targets_from_mongo(mongo_uri, args.mongo_db)
    
    if not config.targets:
        logger.error("No targets found! Use --host or configure MongoDB.")
        return
    
    # Run scraper
    scraper = AgentScraper(config)
    
    if args.once:
        result = scraper.run_once()
        print(json.dumps(result, indent=2))
    else:
        scraper.run_forever()


if __name__ == "__main__":
    main()
