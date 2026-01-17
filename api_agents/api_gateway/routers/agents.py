"""
Agents Router - Agent process management and action triggers
"""
import os
import sys
import subprocess
from fastapi import APIRouter, HTTPException
from ..config import AGENTS_STATE, AGENT_SCRIPTS

router = APIRouter()


@router.get("/agents/status")
def get_agents_status():
    """Get status of background agents"""
    status = {}
    for name, state in AGENTS_STATE.items():
        # Verify if process is actually alive
        is_running = state["running"]
        if state["process"]:
            if state["process"].poll() is not None:
                is_running = False
                state["running"] = False
                state["process"] = None
        
        status[name] = {
            "script": AGENT_SCRIPTS.get(name, ""),
            "running": is_running
        }
    return {"agents": status}


@router.post("/agents/start/{agent_name}")
def start_agent_endpoint(agent_name: str):
    """Start a background agent"""
    agent_key = agent_name.lower()
    
    if agent_key not in AGENTS_STATE:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    state = AGENTS_STATE[agent_key]
    
    # Check if already running
    if state["running"] and state["process"] and state["process"].poll() is None:
        return {"status": "already_running", "agent": agent_name}
    
    # Start process
    try:
        script_rel_path = AGENT_SCRIPTS.get(agent_key)
        if not script_rel_path:
            raise HTTPException(status_code=500, detail="Script path not defined")
        
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', script_rel_path))
        script_dir = os.path.dirname(script_path)
        
        proc = subprocess.Popen(
            [sys.executable, script_path],
            cwd=script_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        AGENTS_STATE[agent_key]["running"] = True
        AGENTS_STATE[agent_key]["process"] = proc
        
        return {
            "status": "started",
            "agent": agent_name,
            "pid": proc.pid,
            "output": ["Agent started in background", f"PID: {proc.pid}"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/stop/{agent_name}")
def stop_agent_endpoint(agent_name: str):
    """Stop a running agent"""
    agent_key = agent_name.lower()
    
    if agent_key not in AGENTS_STATE:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    state = AGENTS_STATE[agent_key]
    
    if not state["running"] or not state["process"]:
        return {"status": "not_running", "agent": agent_name}
    
    try:
        state["process"].terminate()
        try:
            state["process"].wait(timeout=5)
        except subprocess.TimeoutExpired:
            state["process"].kill()
        
        AGENTS_STATE[agent_key]["running"] = False
        AGENTS_STATE[agent_key]["process"] = None
        
        return {"status": "stopped", "agent": agent_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Action Triggers (One-shot agent execution)
# =============================================================================

@router.post("/action/scan")
def trigger_scan():
    """Trigger Scout Agent"""
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../workers/Scout/scout_agent.py'))
        subprocess.Popen(
            [sys.executable, script_path, "--once"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"status": "Scout Agent Triggered via Async Subprocess"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action/auto-discovery")
def trigger_auto_discovery():
    """Backwards-compatible alias for auto-discovery"""
    return trigger_scan()


@router.post("/action/check")
def trigger_check():
    """Trigger CriticalAlert Agent"""
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../workers/CriticalAlert/critical_alert_agent.py'))
        email = os.getenv("ALERT_EMAIL") or os.getenv("SMTP_USER") or "admin@nexi.com"
        subprocess.Popen(
            [sys.executable, script_path, "--email", email, "--once"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"status": "CriticalAlert Agent Triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action/collect")
def trigger_collect():
    """Trigger Collector Agent"""
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../workers/Collector/collector_agent.py'))
        subprocess.Popen(
            [sys.executable, script_path, "--once"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"status": "Collector Agent Triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action/watcher")
def trigger_watcher_once():
    """Trigger Watcher agent for a single scan"""
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../workers/Watcher/watcher_agent.py'))
        subprocess.Popen(
            [sys.executable, script_path, "--once"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"status": "Watcher Agent Triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action/checkmk-sync")
def trigger_checkmk_sync():
    """Trigger CheckMK Bridge for a single sync"""
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../workers/CheckMK_Bridge/main.py'))
        subprocess.Popen(
            [sys.executable, script_path, "--once"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"status": "CheckMK Bridge Triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action/forensic")
def trigger_forensic_analysis():
    """Trigger Forensic AI Analyzer for a single run"""
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../workers/Watcher/ai_analyzer.py'))
        subprocess.Popen(
            [sys.executable, script_path, "--once"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"status": "Forensic Analyzer Triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
