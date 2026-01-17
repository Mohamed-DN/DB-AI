"""
System Router - System status, config, and root endpoints
"""
import os
import subprocess
import shutil
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..dependencies import get_mongo

router = APIRouter()


@router.get("/")
def read_root():
    """Root endpoint"""
    return {"status": "Nexi AI CMDB Backend Running"}


@router.get("/api/system/status")
def get_system_status():
    """Get global system status (RUNNING/PAUSED)"""
    try:
        mongo = get_mongo()
        conf = mongo.execute_eval("db.system_config.findOne({key: 'global_status'})")
        status = conf.get('value', 'RUNNING') if conf else 'RUNNING'
        return {"status": status, "paused": status == "PAUSED"}
    except:
        return {"status": "RUNNING", "paused": False}


@router.post("/api/system/status")
def set_system_status(item: dict):
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

    def event_generator():
        # Update MongoDB global status first
        try:
            mongo = get_mongo()
            if mongo:
                mongo.execute_eval(f"db.system_config.updateOne({{key: 'global_status'}}, {{$set: {{value: '{status}'}}}}, {{upsert: true}})")
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
def get_config():
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
        mongo = get_mongo()
        if not mongo:
            raise Exception("MongoProxy not initialized")
        for agent in agents:
            doc = mongo.execute_eval(f"db.system_config.findOne({{key: '{agent}_interval'}})")
            config[f"{agent}_interval"] = doc.get('value', defaults[agent]) if doc else defaults[agent]
        return config
    except:
        return {f"{a}_interval": defaults[a] for a in agents}


@router.post("/api/config")
def update_config(cfg: dict):
    """Update agent intervals"""
    try:
        mongo = get_mongo()
        if not mongo:
            raise HTTPException(status_code=500, detail="MongoProxy not initialized")
        
        for key, value in cfg.items():
            if not key.endswith('_interval'):
                continue
            try:
                normalized = int(value)
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail=f"Invalid value for {key}")
            if normalized < 5:
                raise HTTPException(status_code=400, detail=f"Interval too small for {key}")
            
            mongo.execute_eval(
                f"db.system_config.updateOne({{key: '{key}'}}, {{$set: {{value: {normalized}}}}}, {{upsert: true}})"
            )
        return {"status": "Updated", "config": cfg}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
