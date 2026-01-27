import sys
import os
sys.path.append(os.getcwd())
from api_agents.workers.discovery.discovery_agent import DiscoveryAgent

agent = DiscoveryAgent()
host_info = {
    "ip_address": "192.168.56.101",
    "db_port": 1521,
    "db_user": "sys",
    "db_password": "root"
}
print("Testing direct Oracle discovery...")
results = agent.discover_oracle_direct(host_info, "gateway-cairo", set())
print(f"Results: {results}")
