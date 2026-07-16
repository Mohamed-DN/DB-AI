"""
Agent Orchestrator - Central entry point for all M-DN DBA AI Agents
Provides unified interface for starting, stopping, and managing agents.
"""
import os
import sys
import argparse
from typing import Dict, Optional, Type

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Agent imports (lazy loaded to avoid circular imports)
AGENT_REGISTRY: Dict[str, dict] = {
    "scout": {
        "module": "api_agents.workers.Scout.scout_agent",
        "class": "ScoutAgent",
        "description": "Discovers databases in Docker environment"
    },
    "collector": {
        "module": "api_agents.workers.Collector.collector_agent",
        "class": "CollectorAgent",
        "description": "Collects deep metrics from databases"
    },
    "watcher": {
        "module": "api_agents.workers.Watcher.watcher_agent",
        "class": "WatcherAgent",
        "description": "Monitors container logs for errors"
    },
    "critical_alert": {
        "module": "api_agents.workers.CriticalAlert.critical_alert_agent",
        "class": "CriticalAlertAgent",
        "description": "Sends email alerts for critical issues"
    },
    "daily_audit": {
        "module": "api_agents.workers.DailyAudit.daily_audit_agent",
        "class": "DailyAuditAgent",
        "description": "Performs daily compliance audits"
    },
    "enricher": {
        "module": "api_agents.workers.Enricher.enricher_agent",
        "class": "EnricherAgent",
        "description": "Updates existing DB records with live data"
    },
    "discovery": {
        "module": "api_agents.workers.Discovery.discovery_agent",
        "class": "DiscoveryAgent",
        "description": "Finds new databases via gateway scanning"
    }
}

def get_agent_class(agent_name: str) -> Optional[Type]:
    """Dynamically load and return agent class"""
    import importlib
    
    if agent_name not in AGENT_REGISTRY:
        print(f"❌ Unknown agent: {agent_name}")
        return None
    
    info = AGENT_REGISTRY[agent_name]
    try:
        module = importlib.import_module(info["module"])
        agent_class = getattr(module, info["class"])
        return agent_class
    except ImportError as e:
        print(f"❌ Failed to import {agent_name}: {e}")
        return None

def start_agent(agent_name: str, once: bool = False):
    """Start a specific agent"""
    agent_class = get_agent_class(agent_name)
    if not agent_class:
        return False
    
    print(f"🚀 Starting {agent_name} agent...")
    agent = agent_class()
    
    if once:
        if hasattr(agent, 'run'):
            agent.run()
        elif hasattr(agent, 'run_once'):
            agent.run_once()
    else:
        if hasattr(agent, 'run_continuous'):
            agent.run_continuous()
        else:
            print(f"⚠️ Agent {agent_name} doesn't support continuous mode")
            if hasattr(agent, 'run'):
                agent.run()
    
    return True

def list_agents():
    """List all available agents"""
    print("\n📋 Available Agents:")
    print("-" * 50)
    for name, info in AGENT_REGISTRY.items():
        print(f"  {name:20} - {info['description']}")
    print("-" * 50)

def main():
    parser = argparse.ArgumentParser(description="M-DN DBA AI Agent Orchestrator")
    parser.add_argument("agent", nargs="?", help="Agent name to run")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--list", action="store_true", help="List available agents")
    
    args = parser.parse_args()
    
    if args.list or not args.agent:
        list_agents()
        return
    
    agent_name = args.agent.lower().replace("-", "_")
    start_agent(agent_name, args.once)

if __name__ == "__main__":
    main()
