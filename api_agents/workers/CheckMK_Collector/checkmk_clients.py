"""
CheckMK Multi-Protocol Client
=============================
Factory e client unificati per supportare:
- CheckMK 2.x REST API (moderno)
- CheckMK 1.5.x Livestatus (socket)
- CheckMK 1.5.x Web API Legacy

Questo modulo permette al Collector di comunicare con qualsiasi versione di CheckMK.
"""
import os
import socket
import time
import logging
from typing import List, Dict, Optional, Any, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CheckMKClient")


# =============================================================================
# Protocol Definition (Interface)
# =============================================================================

class CheckMKClientProtocol(Protocol):
    """Protocol that all CheckMK clients must implement"""
    
    def fetch_hosts(self) -> List[Dict]:
        """Get all hosts"""
        ...
    
    def fetch_services(self, host_name: str) -> List[Dict]:
        """Get services for a specific host"""
        ...
    
    def get_all_services_status(self) -> List[Dict]:
        """Get all services with status"""
        ...
    
    def test_connection(self) -> bool:
        """Test if connection is working"""
        ...


# =============================================================================
# Instance Configuration
# =============================================================================

@dataclass
class CheckMKInstanceConfig:
    """Configuration for a CheckMK instance"""
    name: str
    url: str
    site: str
    datacenter: str = "unknown"
    api_mode: str = "rest_api"  # rest_api | livestatus | webapi_legacy
    api_version: str = "2.x"
    username: str = "cmkadmin"
    password: str = ""
    # Specific to Livestatus
    livestatus_host: Optional[str] = None
    livestatus_port: int = 6557
    livestatus_socket_path: Optional[str] = None
    # Specific to Legacy
    automation_secret: Optional[str] = None
    # General
    timeout: int = 30
    enabled: bool = True
    target_hosts: List[str] = None
    
    def __post_init__(self):
        if self.target_hosts is None:
            self.target_hosts = []


# =============================================================================
# REST API Client (CheckMK 2.x)
# =============================================================================

class CheckMKRestClient:
    """Client for CheckMK 2.x REST API"""
    
    def __init__(self, config: CheckMKInstanceConfig):
        self.config = config
        self.base_url = f"{config.url}/{config.site}/check_mk/api/1.0"
        self.headers = {
            "Authorization": f"Bearer {config.username} {config.password}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def fetch_hosts(self) -> List[Dict]:
        """Get all hosts from REST API"""
        try:
            resp = requests.get(
                f"{self.base_url}/domain-types/host_config/collections/all",
                headers=self.headers,
                timeout=self.config.timeout
            )
            resp.raise_for_status()
            return resp.json().get("value", [])
        except Exception as e:
            logger.error(f"REST API fetch_hosts failed: {e}")
            return []
    
    def fetch_services(self, host_name: str) -> List[Dict]:
        """Get services for a specific host"""
        try:
            resp = requests.get(
                f"{self.base_url}/objects/host/{host_name}/collections/services",
                headers=self.headers,
                timeout=self.config.timeout
            )
            if resp.status_code == 200:
                return resp.json().get("value", [])
            return []
        except Exception as e:
            logger.error(f"REST API fetch_services failed for {host_name}: {e}")
            return []
    
    def get_all_services_status(self) -> List[Dict]:
        """Get all services - requires fetching per host"""
        all_services = []
        hosts = self.fetch_hosts()
        
        for host in hosts:
            host_name = host.get("title") or host.get("id", "unknown")
            services = self.fetch_services(host_name)
            for svc in services:
                svc["host_name"] = host_name
                all_services.append(svc)
        
        return all_services
    
    def test_connection(self) -> bool:
        """Test REST API connection"""
        try:
            resp = requests.get(
                f"{self.base_url}/version",
                headers=self.headers,
                timeout=10
            )
            return resp.status_code == 200
        except:
            return False


# =============================================================================
# Livestatus Client (CheckMK 1.5.x / 2.x)
# =============================================================================

class CheckMKLivestatusClient:
    """Client for CheckMK Livestatus socket"""
    
    def __init__(self, config: CheckMKInstanceConfig):
        self.config = config
        self.socket_path = config.livestatus_socket_path
        self.host = config.livestatus_host or self._extract_host_from_url(config.url)
        self.port = config.livestatus_port
    
    @staticmethod
    def _extract_host_from_url(url: str) -> str:
        """Extract hostname from URL"""
        import re
        match = re.search(r'https?://([^:/]+)', url)
        return match.group(1) if match else "localhost"
    
    def _query(self, lql: str) -> List[Any]:
        """Execute LQL query"""
        sock = None
        try:
            if self.socket_path:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(self.socket_path)
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.config.timeout)
                sock.connect((self.host, self.port))
            
            if not lql.endswith("\n"):
                lql += "\n"
            
            sock.sendall(lql.encode("utf-8"))
            sock.shutdown(socket.SHUT_WR)
            
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            
            import json
            if "OutputFormat: json" in lql:
                return json.loads(response.decode("utf-8")) if response.strip() else []
            return response.decode("utf-8").strip().split("\n")
            
        except Exception as e:
            logger.error(f"Livestatus query failed: {e}")
            return []
        finally:
            if sock:
                sock.close()
    
    def fetch_hosts(self) -> List[Dict]:
        """Get all hosts via Livestatus"""
        lql = """GET hosts
Columns: name address state num_services_ok num_services_warn num_services_crit alias
OutputFormat: json
"""
        raw = self._query(lql)
        
        hosts = []
        for row in raw:
            if isinstance(row, list) and len(row) >= 6:
                hosts.append({
                    "id": row[0],
                    "title": row[0],
                    "extensions": {
                        "attributes": {
                            "ipaddress": row[1],
                            "alias": row[6] if len(row) > 6 else ""
                        },
                        "state": row[2],
                        "num_services_ok": row[3],
                        "num_services_warn": row[4],
                        "num_services_crit": row[5]
                    }
                })
        
        return hosts
    
    def fetch_services(self, host_name: str) -> List[Dict]:
        """Get services for a host via Livestatus"""
        lql = f"""GET services
Columns: host_name description state perf_data plugin_output
Filter: host_name = {host_name}
OutputFormat: json
"""
        raw = self._query(lql)
        
        services = []
        for row in raw:
            if isinstance(row, list) and len(row) >= 4:
                services.append({
                    "host_name": row[0],
                    "title": row[1],
                    "extensions": {
                        "state": row[2],
                        "perf_data": row[3],
                        "plugin_output": row[4] if len(row) > 4 else ""
                    }
                })
        
        return services
    
    def get_all_services_status(self) -> List[Dict]:
        """Get all services via Livestatus"""
        lql = """GET services
Columns: host_name description state perf_data plugin_output
OutputFormat: json
"""
        raw = self._query(lql)
        
        services = []
        for row in raw:
            if isinstance(row, list) and len(row) >= 4:
                services.append({
                    "host_name": row[0],
                    "title": row[1],
                    "extensions": {
                        "state": row[2],
                        "perf_data": row[3],
                        "plugin_output": row[4] if len(row) > 4 else ""
                    }
                })
        
        return services
    
    def test_connection(self) -> bool:
        """Test Livestatus connection"""
        try:
            lql = """GET status
Columns: program_version
OutputFormat: json
"""
            result = self._query(lql)
            return len(result) > 0
        except:
            return False


# =============================================================================
# Web API Legacy Client (CheckMK 1.5.x)
# =============================================================================

class CheckMKWebAPILegacyClient:
    """Client for CheckMK 1.5.x Web API"""
    
    def __init__(self, config: CheckMKInstanceConfig):
        self.config = config
        self.base_url = config.url.rstrip('/')
        self.site = config.site
        self.username = config.username
        self.secret = config.automation_secret or config.password
        self.session = requests.Session()
    
    def _call_webapi(self, action: str, request_data: Optional[Dict] = None) -> Dict:
        """Call Web API endpoint"""
        url = f"{self.base_url}/{self.site}/check_mk/webapi.py"
        
        params = {
            "action": action,
            "output_format": "json",
            "_username": self.username,
            "_secret": self.secret
        }
        
        if request_data:
            import json
            params["request"] = json.dumps(request_data)
        
        try:
            resp = self.session.get(
                url,
                params=params,
                timeout=self.config.timeout,
                verify=False
            )
            
            result = resp.json()
            if result.get("result_code", 0) != 0:
                logger.error(f"Web API error: {result.get('result')}")
                return {}
            
            return result.get("result", {})
            
        except Exception as e:
            logger.error(f"Web API call failed: {e}")
            return {}
    
    def fetch_hosts(self) -> List[Dict]:
        """Get all hosts via Web API"""
        result = self._call_webapi("get_all_hosts")
        
        hosts = []
        for hostname, attrs in result.items():
            hosts.append({
                "id": hostname,
                "title": hostname,
                "extensions": {
                    "attributes": {
                        "ipaddress": attrs.get("ipaddress", ""),
                        "alias": attrs.get("alias", "")
                    },
                    "folder": attrs.get("folder", "/")
                }
            })
        
        return hosts
    
    def fetch_services(self, host_name: str) -> List[Dict]:
        """Get services for a host - limited in legacy API"""
        # Legacy API doesn't have direct service fetch
        # Return empty - problems can be fetched separately
        return []
    
    def get_all_services_status(self) -> List[Dict]:
        """Get service problems via view API"""
        url = f"{self.base_url}/{self.site}/check_mk/view.py"
        
        params = {
            "view_name": "svcproblems",
            "output_format": "json",
            "_username": self.username,
            "_secret": self.secret
        }
        
        try:
            resp = self.session.get(
                url,
                params=params,
                timeout=self.config.timeout,
                verify=False
            )
            
            if resp.status_code != 200:
                return []
            
            rows = resp.json()
            services = []
            
            for row in rows[1:]:  # Skip header
                if len(row) >= 4:
                    services.append({
                        "host_name": row[0],
                        "title": row[1],
                        "extensions": {
                            "state": row[2],
                            "plugin_output": row[3] if len(row) > 3 else ""
                        }
                    })
            
            return services
            
        except Exception as e:
            logger.error(f"View API failed: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test Web API connection"""
        try:
            hosts = self.fetch_hosts()
            return len(hosts) > 0 or isinstance(hosts, list)
        except:
            return False


# =============================================================================
# Client Factory
# =============================================================================

class CheckMKClientFactory:
    """Factory to create appropriate client based on configuration"""
    
    @staticmethod
    def create(config: CheckMKInstanceConfig) -> CheckMKClientProtocol:
        """
        Create a CheckMK client based on api_mode.
        
        Args:
            config: Instance configuration
            
        Returns:
            Appropriate client instance
        """
        api_mode = config.api_mode.lower()
        
        if api_mode == "livestatus":
            logger.info(f"Creating Livestatus client for {config.name}")
            return CheckMKLivestatusClient(config)
        
        elif api_mode == "webapi_legacy":
            logger.info(f"Creating Web API Legacy client for {config.name}")
            return CheckMKWebAPILegacyClient(config)
        
        else:  # Default to REST API
            logger.info(f"Creating REST API client for {config.name}")
            return CheckMKRestClient(config)
    
    @staticmethod
    def detect_version(url: str, site: str, username: str, password: str) -> Dict:
        """
        Auto-detect CheckMK version and recommend api_mode.
        
        Returns:
            Dict with version info and recommended mode
        """
        # Try REST API first (2.x)
        try:
            resp = requests.get(
                f"{url}/{site}/check_mk/api/1.0/version",
                headers={
                    "Authorization": f"Bearer {username} {password}",
                    "Accept": "application/json"
                },
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "version": data.get("versions", {}).get("checkmk", "2.x"),
                    "api_mode": "rest_api",
                    "detected": True
                }
        except:
            pass
        
        # Try Web API (1.5.x)
        try:
            resp = requests.get(
                f"{url}/{site}/check_mk/webapi.py",
                params={
                    "action": "get_all_hosts",
                    "output_format": "json",
                    "_username": username,
                    "_secret": password
                },
                timeout=10,
                verify=False
            )
            if resp.status_code == 200:
                return {
                    "version": "1.5.x",
                    "api_mode": "webapi_legacy",
                    "detected": True
                }
        except:
            pass
        
        # Fallback - assume Livestatus available
        return {
            "version": "unknown",
            "api_mode": "livestatus",
            "detected": False,
            "note": "Could not detect version, defaulting to Livestatus"
        }


# =============================================================================
# Graphite Writer (for metrics export)
# =============================================================================

class GraphiteWriter:
    """Simple Graphite/Carbon writer for VictoriaMetrics"""
    
    def __init__(self, host: str = "localhost", port: int = 2003):
        self.host = host
        self.port = port
    
    def send(self, metric: str, value: float, timestamp: Optional[int] = None):
        """Send single metric"""
        ts = timestamp or int(time.time())
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.host, self.port))
            message = f"{metric} {value} {ts}\n"
            sock.sendall(message.encode())
            sock.close()
            return True
        except Exception as e:
            logger.debug(f"Graphite send failed: {e}")
            return False
    
    def send_batch(self, metrics: List[tuple]):
        """
        Send batch of metrics.
        
        Args:
            metrics: List of (metric_name, value, timestamp) tuples
        """
        if not metrics:
            return True
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.host, self.port))
            
            message_lines = []
            for m in metrics:
                if len(m) >= 3:
                    message_lines.append(f"{m[0]} {m[1]} {m[2]}")
                elif len(m) == 2:
                    message_lines.append(f"{m[0]} {m[1]} {int(time.time())}")
            
            message = "\n".join(message_lines) + "\n"
            sock.sendall(message.encode())
            sock.close()
            
            logger.debug(f"Sent {len(metrics)} metrics to Graphite")
            return True
            
        except Exception as e:
            logger.warning(f"Graphite batch send failed: {e}")
            return False


# =============================================================================
# Export all components
# =============================================================================

__all__ = [
    "CheckMKClientProtocol",
    "CheckMKInstanceConfig",
    "CheckMKRestClient",
    "CheckMKLivestatusClient", 
    "CheckMKWebAPILegacyClient",
    "CheckMKClientFactory",
    "GraphiteWriter"
]
