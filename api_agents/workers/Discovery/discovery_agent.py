"""
Discovery Agent - Finds NEW databases by scanning gateways and Docker environments.
Scans for containers and network services, fingerprints database engines, creates inventory documents.
"""
import os
import sys
import time
import socket
import argparse
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional, List, Set

# Force UTF-8 for Windows Console
sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from orchestrator.core.mongo_proxy import MongoProxy

# Import template builder from Scout
try:
    from api_agents.workers.Scout.template_loader import build_document
    TEMPLATE_AVAILABLE = True
except ImportError:
    TEMPLATE_AVAILABLE = False
    print("[WARN] template_loader not available - using basic document structure")


class PortScanner:
    """Simple port scanner for database discovery"""
    
    # Common database ports
    DB_PORTS = {
        5432: "POSTGRES",
        5433: "POSTGRES",
        5434: "POSTGRES",
        5435: "POSTGRES",
        5436: "POSTGRES",
        5437: "POSTGRES",
        5438: "POSTGRES",
        1521: "ORACLE",
        1522: "ORACLE",
        3306: "MYSQL",
        27017: "MONGODB",
        6379: "REDIS",
        6333: "QDRANT"
    }
    
    @staticmethod
    def scan_port(host: str, port: int, timeout: float = 2.0) -> bool:
        """Check if a port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    @classmethod
    def scan_host(cls, host: str, ports: List[int] = None) -> Dict[int, str]:
        """Scan a host for open database ports"""
        if ports is None:
            ports = list(cls.DB_PORTS.keys())
        
        open_ports = {}
        for port in ports:
            if cls.scan_port(host, port):
                engine = cls.DB_PORTS.get(port, "UNKNOWN")
                open_ports[port] = engine
        
        return open_ports


class DockerDiscovery:
    """Discovers database containers in Docker"""
    
    @staticmethod
    def list_containers() -> List[Dict]:
        """List all Docker containers with database-like images"""
        try:
            cmd = ["docker", "ps", "-a", "--format", "{{.Names}}|{{.Ports}}|{{.Image}}|{{.Status}}"]
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode('utf-8').strip()
            
            containers = []
            for line in output.split('\n'):
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) >= 4:
                    name, ports, image, status = parts[0], parts[1], parts[2], parts[3]
                    
                    # Identify engine from image name
                    engine = None
                    if "postgres" in image.lower():
                        engine = "POSTGRES"
                    elif "oracle" in image.lower():
                        engine = "ORACLE"
                    elif "mysql" in image.lower() or "mariadb" in image.lower():
                        engine = "MYSQL"
                    elif "mongo" in image.lower() and "express" not in image.lower():
                        engine = "MONGODB"
                    elif "redis" in image.lower():
                        engine = "REDIS"
                    elif "qdrant" in image.lower():
                        engine = "QDRANT"
                    
                    if engine:
                        # Parse port from ports string (e.g., "0.0.0.0:5432->5432/tcp")
                        port = None
                        if "->" in ports:
                            try:
                                port_part = ports.split("->")[0]
                                port = int(port_part.split(":")[-1])
                            except:
                                pass
                        
                        containers.append({
                            "name": name,
                            "engine": engine,
                            "port": port,
                            "image": image,
                            "running": "Up" in status
                        })
            
            return containers
        except Exception as e:
            print(f"❌ Docker discovery error: {e}")
            return []


class DiscoveryAgent:
    """Main Discovery Agent - finds new databases via gateway/Docker scanning"""
    
    def __init__(self):
        self.mongo = MongoProxy()
        print("✅ DiscoveryAgent initialized")
    
    def get_gateways(self) -> List[Dict]:
        """Get all gateways from MongoDB"""
        try:
            gateways = self.mongo.execute_eval("db.gateways.find({}).toArray()")
            return gateways or []
        except Exception as e:
            print(f"❌ Error fetching gateways: {e}")
            return []
    
    def get_existing_db_names(self) -> Set[str]:
        """Get set of existing database unique names"""
        try:
            dbs = self.mongo.execute_eval("db.inventory_databases.find({}, {'identity.db_unique_name': 1}).toArray()")
            names = set()
            for db in (dbs or []):
                name = db.get("identity", {}).get("db_unique_name")
                if name:
                    names.add(name.upper())
            return names
        except Exception as e:
            print(f"❌ Error fetching existing DBs: {e}")
            return set()
    
    def discover_docker(self) -> List[Dict]:
        """Discover databases from Docker containers"""
        print("\n🐳 Scanning Docker for database containers...")
        containers = DockerDiscovery.list_containers()
        
        existing_names = self.get_existing_db_names()
        new_dbs = []
        
        for container in containers:
            name = container["name"]
            # Normalize name to match db_unique_name format
            normalized_name = name.upper().replace("-", "_")
            
            if normalized_name in existing_names:
                print(f"   ⏭️ {name} already in inventory")
                continue
            
            if not container["running"]:
                print(f"   ⏭️ {name} is stopped, skipping")
                continue
            
            print(f"   🆕 NEW: {name} ({container['engine']})")
            new_dbs.append(container)
        
        return new_dbs
    
    def discover_via_gateway(self, gateway: Dict) -> List[Dict]:
        """Discover databases via gateway port scanning"""
        gateway_id = gateway.get("_id", "UNKNOWN")
        host_info = gateway.get("info", {})
        ip = host_info.get("ip_address", "127.0.0.1")
        
        print(f"\n🌉 Scanning gateway: {gateway_id} ({ip})...")
        
        # Get reachable hosts from gateway config
        reachable = gateway.get("reachability", {}).get("accessible_dbs", [])
        print(f"   📋 Known reachable DBs: {len(reachable)}")
        
        # For now, just scan the gateway host itself
        open_ports = PortScanner.scan_host(ip)
        
        discovered = []
        for port, engine in open_ports.items():
            print(f"   🔍 Found {engine} on port {port}")
            discovered.append({
                "host": ip,
                "port": port,
                "engine": engine,
                "gateway_ref": gateway_id
            })
        
        return discovered
    
    def create_inventory_document(self, discovery_info: Dict) -> Dict:
        """Create a hierarchical inventory document from discovery info"""
        name = discovery_info.get("name", f"discovered-{discovery_info.get('port', 0)}")
        engine = discovery_info.get("engine", "UNKNOWN")
        port = discovery_info.get("port", 5432)
        
        # Determine environment from name
        if "dev" in name.lower():
            environment = "DEVELOPMENT"
        elif "stg" in name.lower() or "staging" in name.lower():
            environment = "STAGING"
        elif "prod" in name.lower():
            environment = "PRODUCTION"
        else:
            environment = "UNKNOWN"
        
        # Use template loader if available
        if TEMPLATE_AVAILABLE:
            return build_document(
                engine=engine,
                container_name=name,
                port=port,
                environment=environment,
                gateway_ref=discovery_info.get("gateway_ref")
            )
        else:
            # Basic document structure
            return {
                "metadata": {
                    "extraction_timestamp": datetime.now().isoformat(),
                    "agent_version": "2.0.0",
                    "db_technology": engine,
                    "environment": environment,
                    "discovered_by": "DiscoveryAgent"
                },
                "identity": {
                    "db_unique_name": name.upper().replace("-", "_"),
                    "db_name": name,
                    "family": engine,
                    "engine": engine,
                    "host": discovery_info.get("host", "127.0.0.1"),
                    "gateway_ref": discovery_info.get("gateway_ref")
                },
                "connection": {
                    "port": port,
                    "container": name,
                    "type": "DOCKER"
                },
                "state": {
                    "status": "DISCOVERED",
                    "last_seen": datetime.now().isoformat()
                },
                "created_at": datetime.now().isoformat()
            }
    
    def insert_new_database(self, doc: Dict) -> bool:
        """Insert a new database document into MongoDB"""
        try:
            import json
            doc_json = json.dumps(doc, default=str)
            
            js_cmd = f"db.inventory_databases.insertOne({doc_json})"
            self.mongo.execute_eval(js_cmd)
            
            name = doc.get("identity", {}).get("db_unique_name", "UNKNOWN")
            print(f"   ✅ Inserted {name} into inventory")
            
            # Create alert for new discovery
            alert = {
                "severity": "INFO",
                "state": "INFO",
                "type": "NEW_DB_DISCOVERED",
                "message": f"DiscoveryAgent found new database: {name}",
                "database": name,
                "timestamp": datetime.now().isoformat(),
                "processed": False
            }
            self.mongo.insert_alert(alert)
            
            return True
        except Exception as e:
            print(f"   ❌ Insert error: {e}")
            return False
    
    def run_once(self):
        """Run one discovery cycle"""
        print(f"\n{'='*60}")
        print(f"🔍 Discovery Agent - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        discovered_count = 0
        
        # 1. Docker Discovery
        docker_dbs = self.discover_docker()
        for db_info in docker_dbs:
            doc = self.create_inventory_document(db_info)
            if self.insert_new_database(doc):
                discovered_count += 1
        
        # 2. Gateway Discovery
        gateways = self.get_gateways()
        print(f"\n📡 Found {len(gateways)} gateways to scan")
        
        for gateway in gateways:
            gateway_dbs = self.discover_via_gateway(gateway)
            # Note: Gateway discovery returns port-based info, would need more logic
            # to create unique documents and avoid duplicates
        
        print(f"\n✅ Discovery complete. Found {discovered_count} new databases.")
    
    def get_interval(self, default: int = 600) -> int:
        """Get discovery interval from config"""
        try:
            doc = self.mongo.execute_eval("db.system_config.findOne({key: 'discovery_interval'})")
            if doc and 'value' in doc:
                return int(doc['value'])
        except:
            pass
        return default
    
    def check_pause(self) -> bool:
        """Check if system is paused"""
        try:
            doc = self.mongo.execute_eval("db.system_config.findOne({key: 'global_status'})")
            return doc and doc.get('value') == 'PAUSED'
        except:
            return False
    
    def run_continuous(self, interval: int = 600):
        """Run continuous discovery"""
        print("🔄 Discovery Agent starting continuous mode...")
        while True:
            try:
                if self.check_pause():
                    print("⏸️ System paused. Sleeping...")
                    time.sleep(10)
                    continue
                
                self.run_once()
                actual_interval = self.get_interval(interval)
                print(f"💤 Sleeping for {actual_interval}s...")
                time.sleep(actual_interval)
            except KeyboardInterrupt:
                print("\n🛑 Agent stopped.")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description="Discovery Agent - Finds new databases")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=600, help="Discovery interval (seconds)")
    args = parser.parse_args()
    
    agent = DiscoveryAgent()
    
    if args.once:
        agent.run_once()
    else:
        agent.run_continuous(args.interval)


if __name__ == "__main__":
    main()
