"""
Action Tools for M-DN AI Admin
Allows the AI to perform system administration tasks.
"""
import subprocess
from langchain_core.tools import tool

@tool
def manage_container(container_name: str, action: str) -> str:
    """Manage a Docker container (start, stop, restart).
    
    Args:
        container_name: Name of the container (e.g., 'm-dn-cmdb-mongo', 'm-dn-postgres')
        action: One of 'start', 'stop', 'restart'
        
    Returns:
        Result string indicating success or failure.
    """
    action = action.lower()
    if action not in ['start', 'stop', 'restart']:
        return "Error: Action must be 'start', 'stop', or 'restart'."
    
    # Safety Check: Prevent stopping critical AI infrastructure if possible, but user said "do it all"
    # We will allow it but maybe warn in logs.
    
    try:
        # Using specific path checking to prevent arbitrary command injection if this were public,
        # but for internal admin AI, we trust the LLM's intent to fix things.
        
        cmd = ["docker", action, container_name]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return f"Successfully executed '{action}' on {container_name}."
        else:
            return f"Failed to {action} {container_name}. Error: {result.stderr}"
            
    except Exception as e:
        return f"System Error executing Docker command: {str(e)}"

@tool
def get_container_logs(container_name: str, lines: int = 50) -> str:
    """Get recent logs from a Docker container.
    
    Args:
        container_name: Name of the container
        lines: Number of lines to retrieve (default 50, max 200)
        
    Returns:
        Log output strings
    """
    try:
        lines = min(lines, 200) # Cap at 200 to prevent context overflow
        cmd = ["docker", "logs", "--tail", str(lines), container_name]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, encoding='utf-8', errors='replace')
        
        if result.returncode == 0:
            if not result.stdout and not result.stderr:
                return f"No logs found for {container_name}."
            return f"--- Logs for {container_name} (Last {lines} lines) ---\n{result.stdout}\n{result.stderr}"
        else:
            return f"Failed to get logs for {container_name}. Error: {result.stderr}"
            
    except Exception as e:
        return f"System Error retrieving logs: {str(e)}"

@tool
def check_system_health() -> str:
    """Check overall system health (Docker status).
    
    Returns:
        Summary of running containers.
    """
    try:
        cmd = ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return f"System Container Status:\n{result.stdout}"
        else:
            return "Failed to check system health. Docker might be down."
            
    except Exception as e:
        return f"Error checking system: {str(e)}"
