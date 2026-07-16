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
        email = os.getenv("ALERT_EMAIL") or os.getenv("SMTP_USER") or "admin@m-dn.com"
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


@router.post("/action/sentinel")
def trigger_sentinel():
    """
    Trigger Sentinel Engine - Predictive Anomaly Detection
    
    Runs the full Predictor → Verifier → Action workflow:
    1. Predictor Agent analyzes time-series metrics for anomalies
    2. Verifier Agent classifies predictions as real or false alarms
    3. Action dispatch sends emails based on classification
    """
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../workers/Sentinel/sentinel_workflow.py'))
        subprocess.Popen(
            [sys.executable, script_path, "--once"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"status": "Sentinel Engine Triggered", "workflow": "predict → verify → act"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentinel/status")
def get_sentinel_status():
    """Get last Sentinel run status from MongoDB"""
    try:
        from api_agents.shared.sync_mongo_service import SyncMongoService
        mongo = SyncMongoService.get_instance()
        
        # Get last sentinel alert
        db = mongo.client[mongo.db_name]
        last_alert = db.monitoring_alerts.find_one(
            {"source": "SentinelWorkflow"},
            sort=[("created_at", -1)]
        )
        
        if last_alert:
            return {
                "last_run": last_alert.get("created_at"),
                "last_alert_type": last_alert.get("type"),
                "last_db": last_alert.get("db_name"),
                "status": "active"
            }
        return {"status": "no_runs", "message": "Sentinel has not run yet"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/action/oem-collect")
def trigger_oem_collection():
    """Trigger OEM Collector for Oracle Enterprise Manager metrics"""
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../workers/OEM_Collector/oem_collector.py'))
        subprocess.Popen(
            [sys.executable, script_path, "--once"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"status": "OEM Collector Triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action/rag-ingest")
def trigger_rag_ingestion():
    """Trigger Sentinel RAG Knowledge Ingestion"""
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../workers/Sentinel/sentinel_rag_ingester.py'))
        subprocess.Popen(
            [sys.executable, script_path, "--ingest"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"status": "RAG Ingestion Triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
