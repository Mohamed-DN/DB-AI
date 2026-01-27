"""
Discovery Agent V2 - FULLY AUTONOMOUS Database Discovery
==========================================================
Connects to hosts from gateways via SSH, scans for databases,
fingerprints engines, extracts metadata, and creates MongoDB documents.
"""
import os
import sys
import time
import socket
import argparse
import subprocess
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Set

# Force UTF-8 for Windows Console
sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from orchestrator.core.mongo_proxy import MongoProxy

# Import template builder from Scout
try:
    from api_agents.workers.scout.template_loader import build_document
    TEMPLATE_AVAILABLE = True
except ImportError:
    TEMPLATE_AVAILABLE = False
    print("[WARN] template_loader not available - using basic document structure")

# Optional SSH support
try:
    import paramiko
    SSH_AVAILABLE = True
except ImportError:
    SSH_AVAILABLE = False
    print("[WARN] paramiko not available - SSH discovery disabled. Install: pip install paramiko")


# Database connection libraries
try:
    from pymongo import MongoClient
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    import oracledb
    ORACLEDB_AVAILABLE = True
except ImportError:
    ORACLEDB_AVAILABLE = False
    print("[WARN] oracledb not available - Oracle discovery disabled")



class PortScanner:
    """Network port scanner for database discovery"""
    
    DB_PORTS = {
        5432: "POSTGRES", 5433: "POSTGRES", 5434: "POSTGRES", 
        5435: "POSTGRES", 5436: "POSTGRES", 5437: "POSTGRES", 5438: "POSTGRES",
        1521: "ORACLE", 1522: "ORACLE", 1523: "ORACLE",
        3306: "MYSQL", 3307: "MYSQL",
        27017: "MONGODB", 28017: "MONGODB", 27018: "MONGODB",
        6379: "REDIS", 6380: "REDIS",
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


class SSHConnector:
    """SSH connection handler for remote host access"""
    
    def __init__(self, host: str, username: str, password: str = None, key_path: str = None, port: int = 22):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_path = key_path
        self.client = None
    
    def connect(self) -> bool:
        """Establish SSH connection"""
        if not SSH_AVAILABLE:
            print(f"   ❌ SSH not available (paramiko not installed)")
            return False
        
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.key_path and os.path.exists(self.key_path):
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=self.key_path,
                    timeout=10
                )
            else:
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=10
                )
            
            print(f"   ✅ SSH connected to {self.host}")
            return True
        except Exception as e:
            print(f"   ❌ SSH connection failed: {e}")
            return False
    
    def execute(self, command: str) -> Optional[str]:
        """Execute command on remote host"""
        if not self.client:
            return None
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=30)
            output = stdout.read().decode('utf-8').strip()
            return output
        except Exception as e:
            print(f"   ❌ SSH command error: {e}")
            return None
    
    def close(self):
        """Close SSH connection"""
        if self.client:
            self.client.close()
            self.client = None


class RemoteDiscovery:
    """Discovers databases on remote hosts via SSH"""
    
    @staticmethod
    def discover_docker_remote(ssh: SSHConnector) -> List[Dict]:
        """Discover Docker containers on remote host"""
        output = ssh.execute("docker ps -a --format '{{.Names}}|{{.Ports}}|{{.Image}}|{{.Status}}' 2>/dev/null")
        
        if not output:
            return []
        
        containers = []
        for line in output.split('\n'):
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 4:
                name, ports, image, status = parts[0], parts[1], parts[2], parts[3]
                
                # Identify engine from image
                engine = None
                image_lower = image.lower()
                if "postgres" in image_lower:
                    engine = "POSTGRES"
                elif "oracle" in image_lower:
                    engine = "ORACLE"
                elif "mysql" in image_lower or "mariadb" in image_lower:
                    engine = "MYSQL"
                elif "mongo" in image_lower and "express" not in image_lower:
                    engine = "MONGODB"
                elif "redis" in image_lower:
                    engine = "REDIS"
                elif "qdrant" in image_lower:
                    engine = "QDRANT"
                
                if engine:
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
    
    @staticmethod
    def discover_processes_remote(ssh: SSHConnector) -> List[Dict]:
        """Discover database processes running on remote host"""
        # Check common database processes
        processes = []
        
        # PostgreSQL
        output = ssh.execute("pgrep -f postgres && netstat -tlnp 2>/dev/null | grep postgres || ss -tlnp | grep postgres")
        if output and "postgres" in output.lower():
            # Try to get port from netstat/ss output
            port = 5432  # default
            if ":5432" in output:
                port = 5432
            elif ":543" in output:
                try:
                    port = int(output.split(":543")[1].split()[0][:1]) + 5430
                except:
                    pass
            processes.append({"engine": "POSTGRES", "port": port, "type": "process"})
        
        # Oracle
        output = ssh.execute("pgrep -f 'ora_|oracle' && netstat -tlnp 2>/dev/null | grep 1521 || ss -tlnp | grep 1521")
        if output:
            processes.append({"engine": "ORACLE", "port": 1521, "type": "process"})
        
        # MySQL
        output = ssh.execute("pgrep -f mysql && netstat -tlnp 2>/dev/null | grep mysql || ss -tlnp | grep mysql")
        if output:
            processes.append({"engine": "MYSQL", "port": 3306, "type": "process"})
        
        return processes


class DatabaseMetadataExtractor:
    """Extracts metadata directly from database connections"""
    
    @staticmethod
    def extract_postgres(host: str, port: int, user: str = None, password: str = None) -> Optional[Dict]:
        """Extract PostgreSQL metadata by connecting to the database with multiple credentials"""
        if not PSYCOPG2_AVAILABLE:
            print(f"   ⚠️ psycopg2 not available")
            return None
        
        credentials = []
        # Add provided credentials first
        if user and password:
            credentials.append((user, password))
        
        # Add defaults
        credentials.append(("postgres", os.getenv("POSTGRES_PASSWORD", "nexi2024")))
        credentials.append(("aiauto", os.getenv("AIAUTO_PASSWORD", "nexi2024")))
        
        last_error = None
        
        for pg_user, pg_pass in credentials:
            try:
                print(f"   🔐 Trying Postgres: {pg_user}@... ", end="")
                conn = psycopg2.connect(
                    host=host, port=port, user=pg_user, password=pg_pass,
                    database="postgres", connect_timeout=5
                )
                print("✅")
                cursor = conn.cursor()
                
                data = {}
                
                # System identifier
                try:
                    cursor.execute("SELECT system_identifier FROM pg_control_system();")
                    data["system_identifier"] = str(cursor.fetchone()[0])
                except:
                    pass
                
                # Version
                cursor.execute("SELECT version();")
                data["version_full"] = cursor.fetchone()[0]
                
                # Recovery status
                cursor.execute("SELECT pg_is_in_recovery();")
                data["is_in_recovery"] = cursor.fetchone()[0]
                
                # Max connections
                cursor.execute("SHOW max_connections;")
                data["max_connections"] = int(cursor.fetchone()[0])
                
                # Extensions
                cursor.execute("SELECT extname, extversion FROM pg_extension;")
                data["extensions"] = [{"name": r[0], "version": r[1]} for r in cursor.fetchall()]
                
                # Database size
                cursor.execute("SELECT pg_database_size(current_database());")
                data["size_bytes"] = cursor.fetchone()[0]
                
                # Real DB Name (optional)
                # data["db_name"] = "postgres" 

                conn.close()
                return data
                
            except Exception as e:
                print(f"❌ ({e})")
                last_error = e
                continue
        
        print(f"   ⚠️ PostgreSQL extraction failed: {last_error}")
        return None


class DockerDiscovery:
    """Discovers database containers in local Docker"""
    
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
    """
    FULLY AUTONOMOUS Discovery Agent
    =================================
    1. Reads gateways from MongoDB
    2. For each host on gateway → SSH connects
    3. Scans for databases (Docker, processes, port scan)
    4. Fingerprints DB engine
    5. Connects to DB and extracts metadata
    6. Creates hierarchical JSON document
    7. Inserts into MongoDB
    """
    
    def __init__(self):
        self.mongo = MongoProxy()
        self.db_client = None
        self.default_pg_user = os.getenv("POSTGRES_USER", "postgres")
        self.default_pg_password = os.getenv("POSTGRES_PASSWORD", "nexi2024")
        self.default_ssh_user = os.getenv("SSH_USER", "root")
        self.default_ssh_password = os.getenv("SSH_PASSWORD", "")
        self.default_ssh_key = os.getenv("SSH_KEY_PATH", os.path.expanduser("~/.ssh/id_rsa"))
        print("✅ DiscoveryAgent V2 initialized (Autonomous Mode)")
    
    def _get_db_client(self):
        """Get or create reusable MongoDB client"""
        if not PYMONGO_AVAILABLE:
            return None

        if self.db_client is None:
            try:
                # Use same credentials that worked for insert checks
                # Hardcoded based on what worked in logs (admin/nexi2024)
                self.db_client = MongoClient("mongodb://admin:nexi2024@localhost:28017/")
            except Exception as e:
                print(f"⚠️ Failed to create MongoDB client: {e}")
                return None
        return self.db_client

    def get_gateways(self) -> List[Dict]:
        """Get all gateways from MongoDB"""
        # Try PyMongo first
        try:
            client = self._get_db_client()
            if client:
                db_name = os.environ.get("MONGODB_DB", "nexi_cmdb_v2")
                db = client[db_name]
                gateways = list(db.gateways.find({}))
                print(f"DEBUG: get_gateways (PyMongo) found: {[g.get('_id') for g in (gateways or [])]}")
                return gateways
        except Exception as py_err:
            print(f"⚠️ PyMongo get_gateways failed: {py_err}, falling back to Proxy")
            # If connection failed, invalidate client to retry next time
            self.db_client = None

        try:
            gateways = self.mongo.execute_eval("db.gateways.find({}).toArray()")
            print(f"DEBUG: get_gateways (Proxy) found: {[g.get('_id') for g in (gateways or [])]}")
            return gateways or []
        except Exception as e:
            print(f"❌ Error fetching gateways: {e}")
            return []
    
    def get_gateway_hosts(self, gateway: Dict) -> List[Dict]:
        """Get all target hosts from a gateway"""
        hosts = []
        
        # Check for hosts in gateway config
        target_hosts = gateway.get("target_hosts", [])
        for host in target_hosts:
            if isinstance(host, str):
                hosts.append({"ip_address": host, "ssh_user": self.default_ssh_user})
            elif isinstance(host, dict):
                hosts.append(host)
        
        # Check reachability section
        reachability = gateway.get("reachability", {})
        for db_info in reachability.get("accessible_dbs", []):
            if isinstance(db_info, dict) and "host" in db_info:
                hosts.append({"ip_address": db_info["host"]})
        
        return hosts
    
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
    
    def discover_local_docker(self) -> List[Dict]:
        """Discover databases from local Docker containers"""
        print("\n🐳 Scanning LOCAL Docker for database containers...")
        containers = DockerDiscovery.list_containers()
        
        existing_names = self.get_existing_db_names()
        new_dbs = []
        
        for container in containers:
            name = container["name"]
            normalized_name = name.upper().replace("-", "_")
            
            if normalized_name in existing_names:
                print(f"   ⏭️ {name} already in inventory")
                continue
            
            if not container["running"]:
                print(f"   ⏭️ {name} is stopped, skipping")
                continue
            
            print(f"   🆕 NEW: {name} ({container['engine']})")
            
            # Try to extract metadata immediately
            if container["engine"] == "POSTGRES" and container["port"]:
                metadata = DatabaseMetadataExtractor.extract_postgres(
                    "127.0.0.1", container["port"],
                    self.default_pg_user, self.default_pg_password
                )
                if metadata:
                    container["extracted_metadata"] = metadata
                    print(f"      📊 Extracted: version={metadata.get('version_full', 'N/A')[:30]}...")
            
            new_dbs.append(container)
        
        return new_dbs
    
    def discover_remote_host(self, host_info: Dict, gateway_id: str) -> List[Dict]:
        """Discover databases on a remote host via SSH and Direct Connections"""
        ip = host_info.get("ip_address", "")
        ssh_user = host_info.get("ssh_user", self.default_ssh_user)
        ssh_password = host_info.get("ssh_password", self.default_ssh_password)
        ssh_key = host_info.get("ssh_key_path", self.default_ssh_key)
        
        if not ip or ip == "127.0.0.1":
            return []
        
        discovered = []
        existing_names = self.get_existing_db_names()
        
        print(f"\n🔐 SSH connecting to {ip}...")
        
        ssh = SSHConnector(ip, ssh_user, ssh_password, ssh_key)
        if ssh.connect():
            # 1. Docker containers on remote host
            docker_containers = RemoteDiscovery.discover_docker_remote(ssh)
            for container in docker_containers:
                name = container["name"]
                normalized = name.upper().replace("-", "_")
                if normalized not in existing_names and container["running"]:
                    container["host"] = ip
                    container["gateway_ref"] = gateway_id
                    discovered.append(container)
                    print(f"   🆕 Docker: {name} ({container['engine']})")
            
            # 2. Database processes
            processes = RemoteDiscovery.discover_processes_remote(ssh)
            for proc in processes:
                db_name = f"{ip.replace('.', '-')}-{proc['engine'].lower()}-{proc['port']}"
                normalized = db_name.upper().replace("-", "_")
                if normalized not in existing_names:
                    proc["name"] = db_name
                    proc["host"] = ip
                    proc["gateway_ref"] = gateway_id
                    discovered.append(proc)
                    print(f"   🆕 Process: {proc['engine']} on port {proc['port']}")
            
            # 3. Port scan for any missed databases
            open_ports = PortScanner.scan_host(ip)
            for port, engine in open_ports.items():
                db_name = f"{ip.replace('.', '-')}-{engine.lower()}-{port}"
                normalized = db_name.upper().replace("-", "_")
                if normalized not in existing_names:
                    # Check if we already found this via Docker/process
                    already_found = any(d.get("port") == port for d in discovered)
                    if not already_found:
                        discovered.append({
                            "name": db_name,
                            "host": ip,
                            "port": port,
                            "engine": engine,
                            "gateway_ref": gateway_id
                        })
                        print(f"   🆕 Port scan: {engine} on port {port}")
            ssh.close()
        
        else:
            # Fallback to port scan if SSH fails
            print(f"   ⚠️ SSH failed, falling back to port scan...")
            open_ports = PortScanner.scan_host(ip)
            for port, engine in open_ports.items():
                discovered.append({
                    "name": f"{ip.replace('.', '-')}-{engine.lower()}-{port}",
                    "host": ip,
                    "port": port,
                    "engine": engine,
                    "gateway_ref": gateway_id
                })

        # 4. Direct Oracle connection (Always try if port 1521 is found or just force try)
        oracle_discovered = self.discover_oracle_direct(host_info, gateway_id, existing_names)
        
        # Merge logic: If Oracle found a DB on the same IP:Port, prefer the rich Oracle doc over the generic one
        for o_doc in oracle_discovered:
            # Find and remove any existing generic entry for this host/port
            for i, d_doc in enumerate(discovered):
                if d_doc.get("host") == o_doc.get("host") and d_doc.get("port") == o_doc.get("port"):
                     print(f"   🔄 Upgrading {d_doc.get('name')} -> {o_doc.get('name')} (Rich Metadata)")
                     discovered.pop(i)
                     break
            discovered.append(o_doc)
        
        return discovered
    
    def discover_oracle_direct(self, host_info: Dict, gateway_id: str, existing_names: Set[str]) -> List[Dict]:
        """Discover Oracle databases by connecting directly via oracledb"""
        ip = host_info.get("ip_address", "")
        port = host_info.get("db_port", 1521)
        
        if not ORACLEDB_AVAILABLE:
            print(f"   ⚠️ oracledb not available, skipping Oracle discovery")
            return []
        
        discovered = []
        
        # Determine credentials
        credentials = []
        if host_info.get("db_user"):
            credentials.append((host_info.get("db_user"), host_info.get("db_password", "root")))
        
        # Add defaults requested by user
        credentials.append(("sys", "root"))
        credentials.append(("c##aiauto", "root"))
        credentials.append(("c##aiauto", "nexi2024"))
        
        # Common service names to try
        service_names = ["cdbrac", "pdb1", "ORCL", "XE", "FREE", "ORCLCDB"]
        
        for user, password in credentials:
            # Stop if we found database already with previous credential
            if discovered: break 
            
            for service in service_names:
                try:
                    dsn = f"{ip}:{port}/{service}"
                    print(f"   🔗 ({user}) Trying Oracle: {dsn}...", end="")
                    
                    mode = oracledb.AUTH_MODE_SYSDBA if user.lower() == "sys" else oracledb.DEFAULT_AUTH
                    
                    conn = oracledb.connect(
                        user=user,
                        password=password,
                        dsn=dsn,
                        mode=mode
                    )
                    cursor = conn.cursor()
                    print("✅")
                    
                    # Get CDB info
                    cursor.execute("SELECT DBID, NAME, DB_UNIQUE_NAME, CDB FROM V$DATABASE")
                    row = cursor.fetchone()
                    if not row:
                        conn.close()
                        continue
                    
                    dbid, db_name, db_unique_name, is_cdb = row
                    print(f"      Running on: {db_name} (CDB: {is_cdb})")
                    
                    # Get instance info
                    cursor.execute("SELECT INSTANCE_NAME, HOST_NAME, VERSION_FULL FROM V$INSTANCE")
                    inst_row = cursor.fetchone()
                    instance_name = inst_row[0] if inst_row else db_name
                    host_name = inst_row[1] if inst_row else ip
                    version = inst_row[2] if inst_row else "Unknown"
                    
                    # Check if this CDB is already discovered
                    # Use DB_UNIQUE_NAME as the primary identifier (e.g. CDBRAC) instead of generic
                    cdb_unique = db_unique_name.upper()
                    
                    if cdb_unique not in existing_names:
                        cdb_doc = {
                            "name": cdb_unique, # Use Real Name
                            "host": ip,
                            "port": port,
                            "engine": "ORACLE",
                            "service_name": service,
                            "gateway_ref": gateway_id,
                            "is_cdb": is_cdb == "YES",
                            "dbid": dbid,
                            "instance_name": instance_name,
                            "host_name": host_name,
                            "version": version
                        }
                        discovered.append(cdb_doc)
                        existing_names.add(cdb_unique)
                        print(f"   🆕 CDB Found: {cdb_unique}")
                    
                    # Get RAC instances
                    try:
                        cursor.execute("SELECT INST_ID, INSTANCE_NAME, HOST_NAME, STATUS FROM GV$INSTANCE")
                        rac_instances = cursor.fetchall()
                        if len(rac_instances) > 1:
                            print(f"      🔄 RAC detected: {len(rac_instances)} nodes")
                            for inst in rac_instances:
                                # Use RAC-specific name like CDBRAC_1
                                rac_unique = f"{db_unique_name}_RAC{inst[0]}".upper()
                                if rac_unique not in existing_names:
                                    rac_doc = {
                                        "name": rac_unique,
                                        "host": ip,
                                        "port": port,
                                        "engine": "ORACLE",
                                        "service_name": service,
                                        "gateway_ref": gateway_id,
                                        "is_rac": True,
                                        "instance_id": inst[0],
                                        "instance_name": inst[1],
                                        "rac_host": inst[2],
                                        "rac_status": inst[3]
                                    }
                                    discovered.append(rac_doc)
                                    existing_names.add(rac_unique)
                                    print(f"      🆕 RAC Node: {inst[1]} on {inst[2]}")
                    except:
                        pass
                    
                    # Get PDBs (if CDB)
                    if is_cdb == "YES":
                        try:
                            cursor.execute("""
                                SELECT PDB_ID, PDB_NAME, OPEN_MODE, STATUS 
                                FROM V$PDBS 
                                WHERE PDB_NAME != 'PDB$SEED'
                            """)
                            for pdb_row in cursor.fetchall():
                                pdb_name = pdb_row[1]
                                # Use PDB Name as unique identifier if possible, or PDB_CDB
                                # But we must ensure uniqueness. Let's stick to PDB_CDB for safety BUT display as PDB Name
                                pdb_unique = f"{pdb_name}_{db_unique_name}".upper()
                                
                                if pdb_unique not in existing_names:
                                    pdb_doc = {
                                        "name": pdb_name, # Display Name
                                        "db_unique_suffix": pdb_unique, # Internal unique suffix
                                        "host": ip,
                                        "port": port,
                                        "engine": "ORACLE",
                                        "service_name": pdb_name.lower(),
                                        "gateway_ref": gateway_id,
                                        "is_pdb": True,
                                        "parent_cdb": db_unique_name,
                                        "pdb_id": pdb_row[0],
                                        "open_mode": pdb_row[2],
                                        "status": pdb_row[3]
                                    }
                                    discovered.append(pdb_doc)
                                    existing_names.add(pdb_unique)
                                    print(f"      🆕 PDB: {pdb_name} ({pdb_row[2]})")
                        except Exception as e:
                            print(f"      ⚠️ PDB query error: {str(e)[:40]}")
                    
                    conn.close()
                    break  # Success, stop trying other services with this credential
                    
                except Exception as e:
                    print(f"❌")
                    # Try next service name
                    continue
        
        return discovered
    
    def create_inventory_document(self, discovery_info: Dict) -> Dict:
        """Create a hierarchical inventory document from discovery info"""
        name = discovery_info.get("name", f"discovered-{discovery_info.get('port', 0)}")
        engine = discovery_info.get("engine", "UNKNOWN")
        port = discovery_info.get("port", 5432)
        host = discovery_info.get("host", "127.0.0.1")
        
        # Determine environment from name
        if "dev" in name.lower():
            environment = "DEVELOPMENT"
        elif "stg" in name.lower() or "staging" in name.lower():
            environment = "STAGING"
        elif "prod" in name.lower():
            environment = "PRODUCTION"
        else:
            environment = "DISCOVERED"
        
        # Build base document
        if TEMPLATE_AVAILABLE:
            doc = build_document(
                engine=engine,
                container_name=name,
                port=port,
                environment=environment,
                gateway_ref=discovery_info.get("gateway_ref")
            )
        else:
            doc = {
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
                    "host": host,
                    "gateway_ref": discovery_info.get("gateway_ref")
                },
                "connection": {
                    "port": port,
                    "container": name,
                    "type": discovery_info.get("type", "DOCKER")
                },
                "state": {
                    "status": "DISCOVERED",
                    "last_seen": datetime.now().isoformat()
                },
                "created_at": datetime.now().isoformat()
            }
        
        # Merge extracted metadata if available
        extracted = discovery_info.get("extracted_metadata", {})
        if extracted:
            if engine == "POSTGRES":
                if "system_identifier" in extracted:
                    doc.setdefault("cluster_identity", {})["system_identifier"] = extracted["system_identifier"]
                if "version_full" in extracted:
                    doc.setdefault("cluster_identity", {})["version_full"] = extracted["version_full"]
                if "is_in_recovery" in extracted:
                    doc.setdefault("instance_details", {})["is_in_recovery"] = extracted["is_in_recovery"]
                if "max_connections" in extracted:
                    doc.setdefault("resource_config", {}).setdefault("connections", {})["max_connections"] = extracted["max_connections"]
                if "extensions" in extracted:
                    doc["extensions_installed"] = extracted["extensions"]
                if "size_bytes" in extracted:
                    doc.setdefault("storage_info", {})["database_size_bytes"] = extracted["size_bytes"]
        
        # Update host in identity if different
        doc.setdefault("identity", {})["host"] = host
        
        return doc
    
    def insert_new_database(self, doc: Dict) -> bool:
        """Insert a new database document into MongoDB"""
        # Try PyMongo direct insertion first (more reliable for large docs)
        try:
            client = self._get_db_client()
            if client:
                db = client["nexi_cmdb_v2"]
                db.inventory_databases.insert_one(doc)

                name = doc.get("identity", {}).get("db_unique_name", "UNKNOWN")
                print(f"   ✅ Inserted {name} into inventory (PyMongo)")

                # Create alert
                alert = {
                    "severity": "INFO",
                    "state": "INFO",
                    "type": "NEW_DB_DISCOVERED",
                    "message": f"DiscoveryAgent found new database: {name}",
                    "database": name,
                    "host": doc.get("identity", {}).get("host"),
                    "engine": doc.get("identity", {}).get("engine"),
                    "timestamp": datetime.now().isoformat(),
                    "processed": False
                }
                db.monitoring_alerts.insert_one(alert)
                return True
        except Exception as e:
            print(f"   ⚠️ PyMongo insert failed: {e}, falling back to Proxy")
            # If connection failed, invalidate client to retry next time
            self.db_client = None

        try:
            doc_json = json.dumps(doc, default=str)
            js_cmd = f"db.inventory_databases.insertOne({doc_json})"
            self.mongo.execute_eval(js_cmd)
            
            name = doc.get("identity", {}).get("db_unique_name", "UNKNOWN")
            print(f"   ✅ Inserted {name} into inventory (Proxy)")
            
            # Create alert
            alert = {
                "severity": "INFO",
                "state": "INFO",
                "type": "NEW_DB_DISCOVERED",
                "message": f"DiscoveryAgent found new database: {name}",
                "database": name,
                "host": doc.get("identity", {}).get("host"),
                "engine": doc.get("identity", {}).get("engine"),
                "timestamp": datetime.now().isoformat(),
                "processed": False
            }
            self.mongo.insert_alert(alert)
            
            return True
        except Exception as e:
            print(f"   ❌ Insert error: {e}")
            return False
    
    def run_once(self):
        """Run one complete discovery cycle"""
        print(f"\n{'='*70}")
        print(f"🔍 Discovery Agent V2 (AUTONOMOUS) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        
        discovered_count = 0
        
        # 1. Local Docker Discovery
        docker_dbs = self.discover_local_docker()
        for db_info in docker_dbs:
            db_info["host"] = "127.0.0.1"
            doc = self.create_inventory_document(db_info)
            if self.insert_new_database(doc):
                discovered_count += 1
        
        # 2. Gateway-based Remote Discovery
        gateways = self.get_gateways()
        print(f"\n📡 Found {len(gateways)} gateways to scan")
        
        for gateway in gateways:
            gateway_id = str(gateway.get("_id", "UNKNOWN"))
            print(f"\n🌉 Gateway: {gateway_id}")
            
            # Get target hosts from gateway
            hosts = self.get_gateway_hosts(gateway)
            print(f"   📋 {len(hosts)} target hosts configured")
            
            for host_info in hosts:
                remote_dbs = self.discover_remote_host(host_info, gateway_id)
                for db_info in remote_dbs:
                    doc = self.create_inventory_document(db_info)
                    if self.insert_new_database(doc):
                        discovered_count += 1
        
        print(f"\n✅ Discovery complete. Found and inserted {discovered_count} new databases.")
        return discovered_count
    
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
        print("🔄 Discovery Agent V2 starting AUTONOMOUS continuous mode...")
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
    parser = argparse.ArgumentParser(description="Discovery Agent V2 - Autonomous Database Discovery")
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
