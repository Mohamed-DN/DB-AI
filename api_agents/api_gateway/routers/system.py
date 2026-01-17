"""
System Router - System status, config, and root endpoints (Async with Motor)
"""
import os
import subprocess
import shutil
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from ..services.mongo_service import get_mongo_service

router = APIRouter()

# Paths to artifacts (hardcoded relative to user home or project)
# Adjust these based on the actual environment
ARTIFACTS_DIR = r"C:\Users\Mohamed\.gemini\antigravity\brain\62e0278a-33eb-4dfd-956c-7dcaae10fe92"
TASK_PATH = os.path.join(ARTIFACTS_DIR, "task.md")
WALKTHROUGH_PATH = os.path.join(ARTIFACTS_DIR, "walkthrough.md")
PLAN_PATH = os.path.join(ARTIFACTS_DIR, "implementation_plan.md")


@router.get("/", response_class=HTMLResponse)
async def read_root():
    """Root endpoint with Dashboard"""
    
    # Get System Status
    try:
        mongo = get_mongo_service()
        status = await mongo.get_config("global_status") or "RUNNING"
        db_count = await mongo.count_databases()
        alert_count = await mongo.count_critical_alerts()
    except:
        status = "UNKNOWN"
        db_count = "?"
        alert_count = "?"

    # Check Artifacts Existence
    has_task = os.path.exists(TASK_PATH)
    has_walkthrough = os.path.exists(WALKTHROUGH_PATH)
    has_plan = os.path.exists(PLAN_PATH)

    # Read Task Progress (Simple Parsing)
    tasks_html = ""
    if has_task:
        try:
            with open(TASK_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
                completed = 0
                total = 0
                pending_tasks = []
                for line in lines:
                    if "- [x]" in line:
                        completed += 1
                        total += 1
                    elif "- [ ]" in line:
                        total += 1
                        if len(pending_tasks) < 5:
                            pending_tasks.append(line.replace("- [ ]", "").strip())
                
                progress = int((completed / total) * 100) if total > 0 else 0
                
                tasks_html = f"""
                <div class="card">
                    <h2>📋 Project Progress: {progress}%</h2>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {progress}%"></div>
                    </div>
                    <p><strong>Completed:</strong> {completed}/{total} tasks</p>
                    <h3>Next Tasks:</h3>
                    <ul>
                        {''.join(f'<li>{t}</li>' for t in pending_tasks)}
                    </ul>
                </div>
                """
        except:
            tasks_html = "<p>Error reading task file</p>"

    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Nexi AI CMDB Dashboard</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f0f2f5; color: #333; }}
            .container {{ max-width: 1000px; margin: 40px auto; padding: 20px; }}
            h1 {{ color: #004d40; text-align: center; }}
            .status-banner {{ background-color: { '#4caf50' if status == 'RUNNING' else '#ff9800' }; color: white; padding: 15px; text-align: center; border-radius: 8px; margin-bottom: 20px; font-weight: bold; font-size: 1.2em; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
            .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            h2 {{ margin-top: 0; color: #00796b; border-bottom: 2px solid #e0f2f1; padding-bottom: 10px; }}
            .metric {{ font-size: 2em; font-weight: bold; color: #004d40; }}
            .metric-label {{ color: #666; }}
            .path-box {{ background: #263238; color: #eceff1; padding: 10px; border-radius: 4px; font-family: monospace; overflow-x: auto; font-size: 0.9em; margin-bottom: 10px; }}
            .progress-bar {{ background: #e0e0e0; border-radius: 10px; height: 10px; width: 100%; margin: 10px 0; }}
            .progress-fill {{ background: #009688; height: 100%; border-radius: 10px; transition: width 0.3s ease; }}
            ul {{ padding-left: 20px; }}
            li {{ margin-bottom: 5px; }}
            .btn {{ display: inline-block; padding: 10px 20px; background: #00796b; color: white; text-decoration: none; border-radius: 5px; margin-right: 10px; }}
            .btn:hover {{ background: #004d40; }}
        </style>
        <meta http-equiv="refresh" content="30">
    </head>
    <body>
        <div class="container">
            <h1>🚀 Nexi AI CMDB Dashboard</h1>
            
            <div class="status-banner">
                System Status: {status}
            </div>
            
            <div class="grid">
                <!-- Metrics Card -->
                <div class="card">
                    <h2>📊 System Overview</h2>
                    <div>
                        <span class="metric">{db_count}</span>
                        <span class="metric-label">Databases</span>
                    </div>
                    <div>
                        <span class="metric" style="color: {'red' if isinstance(alert_count, int) and alert_count > 0 else 'green'}">{alert_count}</span>
                        <span class="metric-label">Critical Alerts</span>
                    </div>
                    <p><strong>Environment:</strong> Production</p>
                    <p><strong>Version:</strong> v3.1.0</p>
                </div>

                <!-- Progress Card -->
                {tasks_html}
            </div>

            <br>

            <div class="card">
                <h2>📂 Project Artifacts</h2>
                <p>Use these paths to access documentation:</p>
                
                <h3>Implementation Plan</h3>
                <div class="path-box">{PLAN_PATH if has_plan else "Not found"}</div>
                
                <h3>Task List</h3>
                <div class="path-box">{TASK_PATH if has_task else "Not found"}</div>
                
                <h3>Walkthrough</h3>
                <div class="path-box">{WALKTHROUGH_PATH if has_walkthrough else "Not found"}</div>
                
                <p>
                    <a href="/docs" class="btn">📚 API Documentation</a>
                    <a href="/redoc" class="btn">📖 ReDoc</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/api/system/status")
async def get_system_status():
    """Get global system status (RUNNING/PAUSED)"""
    try:
        mongo = get_mongo_service()
        status = await mongo.get_config("global_status")
        status = status or "RUNNING"
        return {"status": status, "paused": status == "PAUSED"}
    except:
        return {"status": "RUNNING", "paused": False}


@router.post("/api/system/status")
async def set_system_status(item: dict):
    """Set global system status (RUNNING/PAUSED) - Controls Docker Lab containers with Streaming Progress"""
    status = item.get("status", "RUNNING").upper()
    if status not in ["RUNNING", "PAUSED"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    # Container suffix from environment
    suffix = os.getenv('GATEWAY_SUFFIX', '2')
    
    lab_containers = [
        f"nexi-mongodb{suffix}",
        f"nexi-redis{suffix}",
        f"nexi-ollama{suffix}",
        f"nexi-qdrant{suffix}",
        f"nexi-gw-milano{suffix}",
        f"nexi-gw-bratislava{suffix}",
        f"nexi-gw-cairo{suffix}",
        f"nexi-pg-milano-prod{suffix}",
        f"nexi-pg-milano-dev{suffix}",
        f"nexi-pg-milano-stg{suffix}",
        f"nexi-pg-bratislava-prod{suffix}",
        f"nexi-pg-bratislava-dev{suffix}",
        f"nexi-oracle-cairo-primary{suffix}",
        f"nexi-oracle-cairo-replica{suffix}",
        f"nexi-mongo-express{suffix}",
        f"nexi-grafana{suffix}",
        f"nexi-prometheus{suffix}",
        f"nexi-langfuse{suffix}",
    ]
    
    docker_cmd = shutil.which("docker") or "/usr/local/bin/docker"
    action = "stop" if status == "PAUSED" else "start"

    async def event_generator():
        # Update MongoDB global status first
        try:
            mongo = get_mongo_service()
            await mongo.set_config("global_status", status)
        except:
            pass

        # Yield initial event
        yield json.dumps({"type": "start", "action": action, "total": len(lab_containers)}) + "\n"

        success_count = 0
        
        for container in lab_containers:
            try:
                yield json.dumps({"type": "progress", "container": container, "status": "pending"}) + "\n"
                
                cmd = [docker_cmd, action, container]
                result = subprocess.run(cmd, capture_output=True, timeout=30, text=True)
                success = result.returncode == 0
                if success:
                    success_count += 1
                
                yield json.dumps({
                    "type": "progress",
                    "container": container,
                    "status": "done" if success else "failed",
                    "message": result.stdout.strip() if success else result.stderr.strip()
                }) + "\n"
                
            except Exception as e:
                yield json.dumps({
                    "type": "progress",
                    "container": container,
                    "status": "failed",
                    "message": str(e)
                }) + "\n"
        
        yield json.dumps({
            "type": "complete",
            "status": status,
            "success_count": success_count,
            "total": len(lab_containers)
        }) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@router.get("/api/config")
async def get_config():
    """Get all agent intervals"""
    agents = ['scout', 'criticalalert', 'watcher', 'forensicanalyzer', 'checkmk_bridge', 'collector']
    defaults = {
        'scout': 60, 
        'criticalalert': 30, 
        'watcher': 10, 
        'forensicanalyzer': 30, 
        'checkmk_bridge': 60, 
        'collector': 30
    }
    
    config = {}
    try:
        mongo = get_mongo_service()
        for agent in agents:
            value = await mongo.get_config(f"{agent}_interval")
            config[f"{agent}_interval"] = value if value is not None else defaults[agent]
        return config
    except:
        return {f"{a}_interval": defaults[a] for a in agents}


@router.post("/api/config")
async def update_config(cfg: dict):
    """Update agent intervals"""
    try:
        mongo = get_mongo_service()
        
        for key, value in cfg.items():
            if not key.endswith('_interval'):
                continue
            try:
                normalized = int(value)
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail=f"Invalid value for {key}")
            if normalized < 5:
                raise HTTPException(status_code=400, detail=f"Interval too small for {key}")
            
            await mongo.set_config(key, normalized)
        
        return {"status": "Updated", "config": cfg}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
