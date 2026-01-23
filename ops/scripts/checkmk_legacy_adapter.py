"""
CheckMK 1.5.x Web API Legacy Adapter
====================================
Adapter per comunicare con CheckMK 1.5.x usando la vecchia Web API.
Converte le risposte legacy in formato REST API 2.x compatibile.

La Web API 1.5.x usa:
- Autenticazione cookie-based o automation secret
- Formato risposta: JSON con struttura diversa dalla REST API
- Endpoint: /SITE/check_mk/webapi.py?action=...

Usage:
    client = CheckMKLegacyClient(
        base_url="http://cmk-server:8080",
        site="nexi_monitor",
        username="cmkadmin",
        password="secret"
    )
    hosts = client.get_all_hosts()
"""
import os
import re
import json
import logging
import hashlib
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CheckMKLegacyAdapter")


@dataclass
class LegacyConfig:
    """Configuration for CheckMK 1.5.x connection"""
    base_url: str
    site: str
    username: str
    password: str  # Can be password or automation secret
    use_automation_secret: bool = True
    timeout: int = 30
    verify_ssl: bool = False


class CheckMKLegacyError(Exception):
    """Custom exception for legacy API errors"""
    pass


class CheckMKLegacyClient:
    """
    Client per CheckMK 1.5.x Web API.
    Supporta sia autenticazione cookie che automation secret.
    """
    
    def __init__(
        self,
        base_url: str,
        site: str,
        username: str,
        password: str,
        use_automation_secret: bool = True,
        timeout: int = 30,
        verify_ssl: bool = False
    ):
        self.config = LegacyConfig(
            base_url=base_url.rstrip('/'),
            site=site,
            username=username,
            password=password,
            use_automation_secret=use_automation_secret,
            timeout=timeout,
            verify_ssl=verify_ssl
        )
        
        # Setup session with retry logic
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        
        self._logged_in = False
    
    def _get_webapi_url(self) -> str:
        """Get Web API endpoint URL"""
        return f"{self.config.base_url}/{self.config.site}/check_mk/webapi.py"
    
    def _login(self) -> bool:
        """
        Login using cookie-based authentication.
        Only needed if not using automation secret.
        """
        if self.config.use_automation_secret:
            return True
        
        if self._logged_in:
            return True
        
        login_url = f"{self.config.base_url}/{self.config.site}/check_mk/login.py"
        
        try:
            resp = self.session.post(
                login_url,
                data={
                    "_username": self.config.username,
                    "_password": self.config.password,
                    "_login": "1"
                },
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )
            
            if resp.status_code == 200 and "side.py" in resp.text:
                self._logged_in = True
                logger.info("Successfully logged in to CheckMK")
                return True
            else:
                logger.error("Login failed")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def _call_webapi(self, action: str, request_data: Optional[Dict] = None) -> Dict:
        """
        Call Web API endpoint.
        
        Args:
            action: API action (e.g., "get_all_hosts")
            request_data: Optional request data dict
            
        Returns:
            API response dict
        """
        if not self.config.use_automation_secret:
            if not self._login():
                raise CheckMKLegacyError("Failed to login")
        
        params = {
            "action": action,
            "output_format": "json",
            "_username": self.config.username,
            "_secret": self.config.password  # Automation secret
        }
        
        if request_data:
            params["request"] = json.dumps(request_data)
        
        try:
            resp = self.session.get(
                self._get_webapi_url(),
                params=params,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )
            
            if resp.status_code != 200:
                raise CheckMKLegacyError(f"API returned {resp.status_code}: {resp.text[:200]}")
            
            # Parse response
            result = resp.json()
            
            # Check for API-level error
            if result.get("result_code", 0) != 0:
                raise CheckMKLegacyError(f"API error: {result.get('result', 'Unknown error')}")
            
            return result.get("result", {})
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response: {e}")
            raise CheckMKLegacyError(f"Invalid JSON response: {e}")
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise CheckMKLegacyError(f"Request failed: {e}")
    
    def get_all_hosts(self) -> List[Dict]:
        """
        Get all hosts in REST-API 2.x compatible format.
        
        Returns:
            List of host dicts matching CheckMK 2.x structure
        """
        try:
            result = self._call_webapi("get_all_hosts")
            
            hosts = []
            for hostname, attrs in result.items():
                hosts.append({
                    "id": hostname,
                    "title": hostname,
                    "extensions": {
                        "attributes": {
                            "ipaddress": attrs.get("ipaddress", ""),
                            "alias": attrs.get("alias", hostname),
                            "tag_agent": attrs.get("tag_agent", "cmk-agent"),
                            "tag_criticality": attrs.get("tag_criticality", "prod")
                        },
                        "folder": attrs.get("folder", "/")
                    }
                })
            
            logger.info(f"Retrieved {len(hosts)} hosts from Web API")
            return hosts
            
        except Exception as e:
            logger.error(f"Failed to get hosts: {e}")
            return []
    
    def get_host_services(self, hostname: str) -> List[Dict]:
        """
        Get services for a specific host.
        Note: Web API 1.5.x doesn't have direct service listing.
        This uses the view API as fallback.
        
        Args:
            hostname: Host name
            
        Returns:
            List of service dicts
        """
        # Try using the view API
        view_url = f"{self.config.base_url}/{self.config.site}/check_mk/view.py"
        
        params = {
            "view_name": "svcproblems",
            "host": hostname,
            "output_format": "json",
            "_username": self.config.username,
            "_secret": self.config.password
        }
        
        try:
            resp = self.session.get(
                view_url,
                params=params,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )
            
            if resp.status_code == 200:
                try:
                    rows = resp.json()
                    services = []
                    for row in rows[1:]:  # Skip header row
                        if len(row) >= 4:
                            services.append({
                                "host_name": hostname,
                                "title": row[1] if len(row) > 1 else "unknown",
                                "extensions": {
                                    "state": row[2] if len(row) > 2 else 3,
                                    "plugin_output": row[3] if len(row) > 3 else ""
                                }
                            })
                    return services
                except:
                    pass
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get services for {hostname}: {e}")
            return []
    
    def get_service_problems(self) -> List[Dict]:
        """
        Get all service problems using the view API.
        
        Returns:
            List of problematic services
        """
        view_url = f"{self.config.base_url}/{self.config.site}/check_mk/view.py"
        
        params = {
            "view_name": "svcproblems",
            "output_format": "json",
            "_username": self.config.username,
            "_secret": self.config.password
        }
        
        try:
            resp = self.session.get(
                view_url,
                params=params,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )
            
            if resp.status_code != 200:
                logger.error(f"View API returned {resp.status_code}")
                return []
            
            rows = resp.json()
            problems = []
            
            # Parse rows (first row is headers)
            headers = rows[0] if rows else []
            for row in rows[1:]:
                problem = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        problem[headers[i]] = value
                
                problems.append({
                    "host_name": problem.get("host", ""),
                    "service": problem.get("service_description", ""),
                    "state": problem.get("service_state", 3),
                    "state_name": problem.get("service_state_name", "UNKNOWN"),
                    "output": problem.get("service_plugin_output", ""),
                    "last_check": problem.get("service_last_check", "")
                })
            
            logger.info(f"Found {len(problems)} service problems")
            return problems
            
        except Exception as e:
            logger.error(f"Failed to get service problems: {e}")
            return []
    
    def discover_services(self, hostname: str) -> bool:
        """
        Trigger service discovery for a host.
        
        Args:
            hostname: Host name
            
        Returns:
            True if successful
        """
        try:
            self._call_webapi("discover_services", {"hostname": hostname})
            logger.info(f"Service discovery triggered for {hostname}")
            return True
        except Exception as e:
            logger.error(f"Failed to discover services: {e}")
            return False
    
    def activate_changes(self, sites: Optional[List[str]] = None) -> bool:
        """
        Activate configuration changes.
        
        Args:
            sites: Optional list of sites to activate
            
        Returns:
            True if successful
        """
        try:
            request_data = {}
            if sites:
                request_data["sites"] = sites
            
            self._call_webapi("activate_changes", request_data)
            logger.info("Changes activated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to activate changes: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test if Web API is accessible.
        
        Returns:
            True if connection successful
        """
        try:
            hosts = self.get_all_hosts()
            logger.info(f"Web API connection OK - {len(hosts)} hosts found")
            return True
        except Exception as e:
            logger.error(f"Web API connection test failed: {e}")
            return False


# =============================================================================
# Adapter Interface (for Collector compatibility)
# =============================================================================

class LegacyRestAdapter:
    """
    Adapter that wraps CheckMKLegacyClient to provide REST-API-like interface.
    This allows the CheckMK Collector to work with both 1.5.x and 2.x seamlessly.
    """
    
    def __init__(self, config: LegacyConfig):
        self.client = CheckMKLegacyClient(
            base_url=config.base_url,
            site=config.site,
            username=config.username,
            password=config.password,
            use_automation_secret=config.use_automation_secret,
            timeout=config.timeout,
            verify_ssl=config.verify_ssl
        )
        self.site = config.site
    
    def fetch_hosts(self) -> List[Dict]:
        """Mimic REST API fetch_hosts()"""
        return self.client.get_all_hosts()
    
    def fetch_services(self, host_name: str) -> List[Dict]:
        """Mimic REST API fetch_services()"""
        return self.client.get_host_services(host_name)
    
    def get_all_services_status(self) -> List[Dict]:
        """
        Mimic REST API get_all_services_status().
        Note: Legacy API doesn't have bulk service fetch, so we get problems only.
        """
        return self.client.get_service_problems()


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CheckMK 1.5.x Legacy API CLI")
    parser.add_argument("--url", default="http://localhost:8080", help="CheckMK base URL")
    parser.add_argument("--site", default="nexi_monitor", help="CheckMK site name")
    parser.add_argument("--user", default="automation", help="Username")
    parser.add_argument("--secret", required=True, help="Automation secret")
    parser.add_argument("--test", action="store_true", help="Test connection")
    parser.add_argument("--hosts", action="store_true", help="List all hosts")
    parser.add_argument("--services", help="List services for host")
    parser.add_argument("--problems", action="store_true", help="List service problems")
    
    args = parser.parse_args()
    
    client = CheckMKLegacyClient(
        base_url=args.url,
        site=args.site,
        username=args.user,
        password=args.secret
    )
    
    if args.test:
        if client.test_connection():
            print("✅ Connection successful")
        else:
            print("❌ Connection failed")
    
    elif args.hosts:
        hosts = client.get_all_hosts()
        print(json.dumps(hosts, indent=2))
    
    elif args.services:
        services = client.get_host_services(args.services)
        print(json.dumps(services, indent=2))
    
    elif args.problems:
        problems = client.get_service_problems()
        print(json.dumps(problems, indent=2))
    
    else:
        parser.print_help()
