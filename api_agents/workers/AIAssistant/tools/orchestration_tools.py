"""
Orchestration Tools for Nexi AI Admin
Allows the AI to orchestrate other agents and manage infrastructure.
"""
import subprocess
import json
import os
from pathlib import Path
from langchain_core.tools import tool
from typing import List, Optional

# Base path for agent workers
AGENTS_BASE_PATH = Path(__file__).parent.parent.parent

@tool
def run_agent(agent_name: str, mode: str = "once", target: Optional[str] = None) -> str:
    """Run a specific Nexi AI agent.
    
    Args:
        agent_name: Name of the agent ('discovery', 'enricher', 'user_provisioner', 'scout', 'collector')
        mode: Execution mode ('once' for single run, 'continuous' for loop - default 'once')
        target: Optional target for the agent (e.g., specific IP for UserProvisioner)
        
    Returns:
        Output or status of the agent execution.
    """
    agent_map = {
        "discovery": "Discovery/discovery_agent.py",
        "enricher": "Enricher/enricher_agent.py",
        "user_provisioner": "UserProvisioner/user_provisioner_agent.py",
        "scout": "Scout/scout_agent.py",
        "collector": "Collector/collector_agent.py",
        "watcher": "Watcher/watcher_agent.py",
        "critical_alert": "CriticalAlert/critical_alert_agent.py"
    }
    
    script_path = agent_map.get(agent_name.lower())
    if not script_path:
        return f"Error: Agent '{agent_name}' not found. Available: {', '.join(agent_map.keys())}"
    
    full_path = AGENTS_BASE_PATH / script_path
    
    if not full_path.exists():
        return f"Error: Agent script not found at {full_path}"
    
    cmd = ["python", str(full_path)]
    
    if mode == "once":
        cmd.append("--once")
    
    if target:
        if agent_name == "user_provisioner":
             # UserProvisioner accepts --oracle or --postgres
             if "5432" in target:
                 cmd.extend(["--postgres", target])
             else:
                 cmd.extend(["--oracle", target])
    
    try:
        # We run with a timeout to prevent hanging the assistant
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            output_tail = "\n".join(result.stdout.splitlines()[-20:]) # Keep last 20 lines
            return f"✅ Agent '{agent_name}' executed successfully.\nOutput tail:\n{output_tail}"
        else:
            return f"❌ Agent '{agent_name}' failed (Exit {result.returncode}).\nError:\n{result.stderr}"
            
    except subprocess.TimeoutExpired:
        return f"⚠️ Agent '{agent_name}' timed out after 120s (it might be running in background)."
    except Exception as e:
        return f"Error running agent: {str(e)}"

@tool
def list_agents() -> str:
    """List all available Nexi AI agents and their status.
    
    Returns:
        List of agents.
    """
    return """Available Agents:
    - discovery: Scans network/gateways for new databases
    - enricher: Connects to DBs to extract deep metadata (versions, PDBs, schemas)
    - user_provisioner: Creates AI monitoring accounts on DBs
    - scout: High-frequency availability monitoring (up/down)
    - collector: Collects performance metrics (Prometheus)
    - watcher: AI Analyzer for anomaly detection
    - critical_alert: Alert management
    """

@tool
def manage_gateway(action: str, name: str, hosts: Optional[List[str]] = None) -> str:
    """Manage database gateways for discovery.
    
    Args:
        action: 'create', 'delete', 'list'
        name: Name of the gateway (e.g., 'gateway-cairo')
        hosts: List of IP addresses (only for 'create')
    """
    # Note: Real implementation would connect to MongoDB. 
    # For now we'll shell out to a helper or just return a placeholder 
    # since the logic is complex to embed here without full MongoProxy context.
    # But wait, we can import MongoProxy!
    
    try:
        from orchestrator.core.mongo_proxy import MongoProxy
        from datetime import datetime
        mongo = MongoProxy()
        
        if action == "list":
            gateways = mongo.execute_eval("db.gateways.find({}).toArray()")
            if not gateways:
                return "No gateways found."
            return "\n".join([f"- {g['_id']} ({len(g.get('target_hosts',[]))} hosts)" for g in gateways])
            
        elif action == "delete":
            mongo.execute_eval(f"db.gateways.delete_one({{'_id': '{name}'}})")
            return f"Gateway '{name}' deleted."
            
        elif action == "create":
            if not hosts:
                return "Error: hosts list required for creation"
            
            target_hosts = [{"ip_address": h, "ssh_user": "oracle"} for h in hosts]
            
            doc = {
                "_id": name,
                "name": name,
                "target_hosts": target_hosts,
                "created_at": datetime.now().isoformat(),
                "status": "ACTIVE"
            }
            # This is tricky with eval/proxy limited interface, assume simple insert
             # We might need to write a temporary script if MongoProxy doesn't support direct insert of dicts easily via eval string
            return "Gateway creation requires manual script for now (complex object)."
            
    except Exception as e:
        return f"Error managing gateway: {str(e)}"
    
    return "Invalid action."
