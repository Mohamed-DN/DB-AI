"""
Livestatus Adapter per CheckMK 1.5.x
====================================
Converte query Livestatus in formato JSON compatibile con il Collector.
Utilizza il protocollo LQL (Livestatus Query Language) nativo di CheckMK.

Supporta:
- Socket Unix locale (/omd/sites/SITE/tmp/run/live)
- Socket TCP remoto (via xinetd, porta 6557)

Usage:
    client = LivestatusClient(host="cmk-server", port=6557)
    hosts = client.get_hosts()
    services = client.get_services(host="db-server-01")
"""
import socket
import json
import logging
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LivestatusAdapter")


@dataclass
class LivestatusConfig:
    """Configuration for Livestatus connection"""
    socket_path: Optional[str] = None  # Unix socket path
    host: Optional[str] = None          # TCP host
    port: int = 6557                     # TCP port (default Livestatus)
    timeout: int = 30                    # Connection timeout
    site: str = "nexi_monitor"           # CheckMK site name


class LivestatusError(Exception):
    """Custom exception for Livestatus errors"""
    pass


class LivestatusClient:
    """
    Client per comunicare con CheckMK Livestatus.
    Funziona sia con socket Unix che TCP.
    """
    
    def __init__(
        self,
        socket_path: Optional[str] = None,
        host: Optional[str] = None,
        port: int = 6557,
        timeout: int = 30,
        site: str = "nexi_monitor"
    ):
        self.config = LivestatusConfig(
            socket_path=socket_path,
            host=host,
            port=port,
            timeout=timeout,
            site=site
        )
        
        if not socket_path and not host:
            raise LivestatusError("Either socket_path or host must be provided")
    
    def _get_socket(self) -> socket.socket:
        """Create and connect socket"""
        try:
            if self.config.socket_path:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(self.config.timeout)
                sock.connect(self.config.socket_path)
                logger.debug(f"Connected to Unix socket: {self.config.socket_path}")
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.config.timeout)
                sock.connect((self.config.host, self.config.port))
                logger.debug(f"Connected to TCP: {self.config.host}:{self.config.port}")
            return sock
        except socket.error as e:
            raise LivestatusError(f"Failed to connect: {e}")
    
    def query(self, lql: str) -> List[Any]:
        """
        Execute LQL query and return parsed results.
        
        Args:
            lql: Livestatus Query Language string
            
        Returns:
            List of results (format depends on OutputFormat)
        """
        sock = None
        try:
            sock = self._get_socket()
            
            # Ensure query ends with newline
            if not lql.endswith("\n"):
                lql += "\n"
            
            # Send query
            sock.sendall(lql.encode("utf-8"))
            sock.shutdown(socket.SHUT_WR)
            
            # Receive response
            response_chunks = []
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_chunks.append(chunk)
            
            response = b"".join(response_chunks).decode("utf-8")
            
            # Parse JSON if OutputFormat: json was specified
            if "OutputFormat: json" in lql:
                if response.strip():
                    return json.loads(response)
                return []
            
            # Otherwise return raw lines
            return [line for line in response.strip().split("\n") if line]
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return []
        except Exception as e:
            raise LivestatusError(f"Query failed: {e}")
        finally:
            if sock:
                sock.close()
    
    def get_hosts(self) -> List[Dict]:
        """
        Get all hosts in REST-API 2.x compatible format.
        
        Returns:
            List of host dicts matching CheckMK 2.x REST API structure
        """
        lql = """GET hosts
Columns: name address state num_services_ok num_services_warn num_services_crit num_services_unknown alias
OutputFormat: json
"""
        raw = self.query(lql)
        
        hosts = []
        for row in raw:
            if len(row) >= 7:
                hosts.append({
                    "id": row[0],
                    "title": row[0],
                    "extensions": {
                        "attributes": {
                            "ipaddress": row[1],
                            "alias": row[7] if len(row) > 7 else ""
                        },
                        "state": row[2],
                        "num_services_ok": row[3],
                        "num_services_warn": row[4],
                        "num_services_crit": row[5],
                        "num_services_unknown": row[6]
                    }
                })
        
        logger.info(f"Retrieved {len(hosts)} hosts from Livestatus")
        return hosts
    
    def get_services(self, host: Optional[str] = None) -> List[Dict]:
        """
        Get services in REST-API 2.x compatible format.
        
        Args:
            host: Optional hostname to filter services
            
        Returns:
            List of service dicts matching CheckMK 2.x REST API structure
        """
        lql = """GET services
Columns: host_name description state perf_data plugin_output
OutputFormat: json
"""
        if host:
            lql = f"""GET services
Columns: host_name description state perf_data plugin_output
Filter: host_name = {host}
OutputFormat: json
"""
        
        raw = self.query(lql)
        
        services = []
        for row in raw:
            if len(row) >= 4:
                services.append({
                    "host_name": row[0],
                    "id": f"{row[0]};{row[1]}",
                    "title": row[1],
                    "extensions": {
                        "state": row[2],
                        "perf_data": row[3],
                        "plugin_output": row[4] if len(row) > 4 else ""
                    }
                })
        
        logger.info(f"Retrieved {len(services)} services from Livestatus" + 
                   (f" for host {host}" if host else ""))
        return services
    
    def get_service_problems(self) -> List[Dict]:
        """
        Get services with problems (state > 0).
        
        Returns:
            List of problematic services
        """
        lql = """GET services
Columns: host_name description state perf_data plugin_output last_state_change
Filter: state > 0
OutputFormat: json
"""
        raw = self.query(lql)
        
        problems = []
        for row in raw:
            if len(row) >= 5:
                problems.append({
                    "host_name": row[0],
                    "service": row[1],
                    "state": row[2],  # 1=WARN, 2=CRIT, 3=UNKNOWN
                    "state_name": {0: "OK", 1: "WARNING", 2: "CRITICAL", 3: "UNKNOWN"}.get(row[2], "UNKNOWN"),
                    "perf_data": row[3],
                    "output": row[4],
                    "last_state_change": row[5] if len(row) > 5 else None
                })
        
        logger.info(f"Found {len(problems)} service problems")
        return problems
    
    def get_host_stats(self) -> Dict:
        """
        Get aggregated host statistics.
        
        Returns:
            Dict with host counts by state
        """
        lql = """GET hosts
Stats: state = 0
Stats: state = 1
Stats: state = 2
OutputFormat: json
"""
        raw = self.query(lql)
        
        if raw and len(raw[0]) >= 3:
            return {
                "up": raw[0][0],
                "down": raw[0][1],
                "unreachable": raw[0][2],
                "total": sum(raw[0])
            }
        return {"up": 0, "down": 0, "unreachable": 0, "total": 0}
    
    def get_service_stats(self) -> Dict:
        """
        Get aggregated service statistics.
        
        Returns:
            Dict with service counts by state
        """
        lql = """GET services
Stats: state = 0
Stats: state = 1
Stats: state = 2
Stats: state = 3
OutputFormat: json
"""
        raw = self.query(lql)
        
        if raw and len(raw[0]) >= 4:
            return {
                "ok": raw[0][0],
                "warning": raw[0][1],
                "critical": raw[0][2],
                "unknown": raw[0][3],
                "total": sum(raw[0])
            }
        return {"ok": 0, "warning": 0, "critical": 0, "unknown": 0, "total": 0}
    
    def test_connection(self) -> bool:
        """
        Test if Livestatus is accessible.
        
        Returns:
            True if connection successful
        """
        try:
            lql = """GET status
Columns: program_version
OutputFormat: json
"""
            result = self.query(lql)
            if result:
                version = result[0][0] if result[0] else "unknown"
                logger.info(f"Livestatus connection OK - CheckMK version: {version}")
                return True
            return False
        except Exception as e:
            logger.error(f"Livestatus connection test failed: {e}")
            return False


# =============================================================================
# Adapter Interface (for Collector compatibility)
# =============================================================================

class LivestatusRestAdapter:
    """
    Adapter that wraps LivestatusClient to provide REST-API-like interface.
    This allows the CheckMK Collector to work with both 1.5.x and 2.x seamlessly.
    """
    
    def __init__(self, config: LivestatusConfig):
        self.client = LivestatusClient(
            socket_path=config.socket_path,
            host=config.host,
            port=config.port,
            timeout=config.timeout,
            site=config.site
        )
        self.site = config.site
    
    def fetch_hosts(self) -> List[Dict]:
        """Mimic REST API fetch_hosts()"""
        return self.client.get_hosts()
    
    def fetch_services(self, host_name: str) -> List[Dict]:
        """Mimic REST API fetch_services()"""
        return self.client.get_services(host=host_name)
    
    def get_all_services_status(self) -> List[Dict]:
        """Mimic REST API get_all_services_status()"""
        return self.client.get_services()


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Livestatus CLI Adapter")
    parser.add_argument("--host", default="localhost", help="CheckMK host")
    parser.add_argument("--port", type=int, default=6557, help="Livestatus TCP port")
    parser.add_argument("--socket", help="Unix socket path (alternative to host/port)")
    parser.add_argument("--test", action="store_true", help="Test connection only")
    parser.add_argument("--hosts", action="store_true", help="List all hosts")
    parser.add_argument("--services", help="List services for host")
    parser.add_argument("--problems", action="store_true", help="List service problems")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    
    args = parser.parse_args()
    
    client = LivestatusClient(
        socket_path=args.socket,
        host=args.host if not args.socket else None,
        port=args.port
    )
    
    if args.test:
        if client.test_connection():
            print("✅ Connection successful")
        else:
            print("❌ Connection failed")
    
    elif args.hosts:
        hosts = client.get_hosts()
        print(json.dumps(hosts, indent=2))
    
    elif args.services:
        services = client.get_services(host=args.services)
        print(json.dumps(services, indent=2))
    
    elif args.problems:
        problems = client.get_service_problems()
        print(json.dumps(problems, indent=2))
    
    elif args.stats:
        print("Host Stats:", json.dumps(client.get_host_stats(), indent=2))
        print("Service Stats:", json.dumps(client.get_service_stats(), indent=2))
    
    else:
        parser.print_help()
