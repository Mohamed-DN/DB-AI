from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import subprocess
import json
import sys
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment
load_dotenv()

# Import MongoProxy
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from Orchestrator.src.mongo_proxy import MongoProxy
from Orchestrator.config.llm_config import (
    LLM_MODELS, DEFAULT_MODEL, FALLBACK_MODEL, OLLAMA_CONFIG,
    get_model_info, get_recommended_models, get_all_models
)

app = FastAPI(title="Nexi AI CMDB", version="2.0.0", description="AI-Powered Database Management")

# Current LLM model state
current_llm_model = DEFAULT_MODEL

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Proxy
try:
    mongo = MongoProxy()
    print("✅ Backend connected to MongoProxy")
except Exception as e:
    print(f"❌ Backend MongoProxy failed: {e}")
    mongo = None

# Models
class ChatRequest(BaseModel):
    message: str
    model: str = None  # Optional: override current model

class ModelSwitchRequest(BaseModel):
    model: str

@app.get("/")
def read_root():
    return {"status": "Nexi AI CMDB Backend Running"}

@app.get("/api/inventory")
def get_inventory():
    """Get all databases"""
    try:
        if not mongo: raise Exception("MongoProxy not initialized")
        # Fetch using MongoProxy
        dbs = mongo.execute_eval("db.inventory_databases.find({}, {'_id': 0}).toArray()")
        return dbs
    except Exception as e:
        print(f"Error fetching inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
def get_alerts():
    """Get recent alerts"""
    try:
        if not mongo: raise Exception("MongoProxy not initialized")
        # Fetch alerts, sort by timestamp desc, limit 50
        # JS: db.monitoring_alerts.find().sort({timestamp: -1}).limit(50).toArray()
        alerts = mongo.execute_eval("db.monitoring_alerts.find().sort({timestamp: -1}).limit(50).toArray()")
        
        # Convert _id if present (MongoProxy returns JSON/dict, but _id might be object string in JS output 
        # usually MongoProxy handles it if it returns JSON)
        # However, for safety, let's process
        for a in alerts:
            if "_id" in a:
                a["_id"] = str(a["_id"])
        return alerts
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat_with_ai(request: ChatRequest):
    """Interact with Local Ollama with Action Capabilities"""
    import requests
    import json
    
    prompt = request.message
    
    # Context
    try:
        db_count = mongo.execute_eval("db.inventory_databases.countDocuments({})")
        active_alerts = mongo.execute_eval('db.monitoring_alerts.countDocuments({"state": "CRITICAL", "processed": false})')
    except:
        db_count = "Unknown"
        active_alerts = "Unknown"
    
    system_prompt = f"""You are the Nexi DBA AI Assistant, an expert in PostgreSQL and Database Administration.
    
    CRITICAL INSTRUCTIONS:
    1. LANGUAGE: You MUST detect the language of the user's message (e.g., Italian, English) and respond in the SAME language. This is mandatory.
    2. QUERY ADVICE: If the user asks about data or actions, propose specific, optimized SQL queries for PostgreSQL.
    3. TONE: Professional, concise, and helpful.

    Current System State:
    - Total Databases Managed: {db_count}
    - Active Critical Alerts: {active_alerts}
    
    TOOLS AVAILABLE:
    1. send_email: Send an email to a user. Format: {{"action": "send_email", "to": "email_address", "subject": "subject", "body": "message_body"}}
    
    TOOL USAGE:
    - If the user asks to send an email, output ONLY the JSON object.
    - If no action is needed, just reply as a helpful assistant in the user's language.
    """
    try:
        # Determine which model to use
        global current_llm_model
        model_to_use = request.model if request.model else current_llm_model
        
        # Call Ollama with selected model
        response = requests.post(f"{OLLAMA_CONFIG['base_url']}/api/generate", json={
            "model": model_to_use,
            "prompt": f"System: {system_prompt}\nUser: {prompt}\nAssistant:",
            "stream": False,
            "options": OLLAMA_CONFIG.get("options", {})
        }, timeout=OLLAMA_CONFIG.get("timeout", 120))
        
        reply = response.json().get("response", "")
        
        # Check for JSON Action
        clean_reply = reply.strip()
        action_performed = False
        action_result = ""
        
        if clean_reply.startswith("{") and "action" in clean_reply:
            try:
                # Setup Email Sender
                from Agents.CriticalAlert.main import EmailSender
                sender = EmailSender()
                
                # Parse JSON
                data = json.loads(clean_reply)
                if data.get("action") == "send_email":
                    to = data.get("to", "mohamed.d.n.2002@gmail.com")
                    subj = data.get("subject", "Nexi AI Alert")
                    body = data.get("body", "No content")
                    
                    print(f"🤖 AI Action: Sending email to {to}")
                    sender.send_alert(to, subj, body)
                    action_performed = True
                    return f"✅ Action Executed: Email sent to {to}."
            except Exception as e:
                print(f"Action Failed: {e}")
                return f"⚠️ I tried to send the email but failed: {e}"
        
        return reply

    except Exception as e:
        return f"AI Brain Offline: {str(e)}"

@app.post("/api/action/scan")
def trigger_scan():
    """Trigger Scout Agent"""
    try:
        # Path to Scout
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Agents/Scout/main.py'))
        subprocess.Popen([sys.executable, script_path])
        return {"status": "Scout Agent Triggered via Async Subprocess"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/action/check")
def trigger_check():
    """Trigger CriticalAlert Agent"""
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Agents/CriticalAlert/main.py'))
        email = os.getenv("SMTP_USER", "admin@nexi.com")
        subprocess.Popen([sys.executable, script_path, "--email", email, "--once"])
        return {"status": "CriticalAlert Agent Triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ConfigRequest(BaseModel):
    scout_interval: int
    check_interval: int

@app.get("/api/config")
def get_config():
    """Get System Intervals"""
    try:
        scout = mongo.execute_eval("db.system_config.findOne({key: 'scout_interval'})")
        check = mongo.execute_eval("db.system_config.findOne({key: 'check_interval'})")
        return {
            "scout_interval": scout.get('value', 60) if scout else 60,
            "check_interval": check.get('value', 10) if check else 10
        }
    except:
        return {"scout_interval": 60, "check_interval": 10}

@app.post("/api/config")
def update_config(cfg: ConfigRequest):
    """Update System Intervals"""
    try:
        # Upsert keys
        mongo.execute_eval(f"db.system_config.updateOne({{key: 'scout_interval'}}, {{$set: {{value: {cfg.scout_interval}}}}}, {{upsert: true}})")
        mongo.execute_eval(f"db.system_config.updateOne({{key: 'check_interval'}}, {{$set: {{value: {cfg.check_interval}}}}}, {{upsert: true}})")
        return {"status": "Updated", "config": cfg}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/action/clear_alerts")
def clear_alerts():
    """Mark all pending alerts as processed"""
    try:
        mongo.execute_eval(f"db.monitoring_alerts.updateMany({{processed: false}}, {{$set: {{processed: true}}}})")
        return {"status": "All Pending Alerts Cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/action/connect/{db_name}")
def connect_db(db_name: str, mode: str = "sql"):
    """Open a terminal connection to the DB. Mode: 'sql' or 'bash'."""
    try:
        # Lookup database to get container host
        if not mongo: raise Exception("MongoProxy not initialized")
        
        db_info = mongo.execute_eval(f"db.inventory_databases.findOne({{'identity.db_unique_name': '{db_name}'}})")
        if not db_info:
            raise HTTPException(status_code=404, detail="Database not found")
            
        container = db_info.get('identity', {}).get('db_name')
        if not container:
             raise HTTPException(status_code=404, detail="Container name not found for database")
            
        # Determine command based on mode
        engine = db_info.get('identity', {}).get('engine', 'POSTGRES').upper()

        if mode == "bash":
            # Use PowerShell to host the Bash session
            cmd = f'start powershell -NoExit -Command "Write-Host \'Starting Linux Shell (Docker)...\' -ForegroundColor Cyan; docker exec -it {container} bash"'
        else:
            # SQL Mode
            if engine == 'ORACLE':
                # Oracle SQLPlus as SYSDBA
                cmd = f'start powershell -NoExit -Command "Write-Host \'Starting Oracle SQLPlus (SYSDBA)...\' -ForegroundColor Red; docker exec -it {container} sqlplus sys/nexi2024 as sysdba"'
            else:
                # Default to PostgreSQL
                cmd = f'start powershell -NoExit -Command "Write-Host \'Starting PostgreSQL Console...\' -ForegroundColor Green; docker exec -it {container} psql -U postgres"'
        
        subprocess.Popen(cmd, shell=True)
        return {"status": f"Terminal ({mode}) opened for {container}"}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/inventory/{db_name}")
def delete_database(db_name: str):
    """Delete a database from inventory (does not stop container)"""
    try:
        if not mongo: raise Exception("MongoProxy not initialized")
        
        # Check if exists
        exists = mongo.execute_eval(f"db.inventory_databases.findOne({{'identity.db_unique_name': '{db_name}'}})")
        if not exists:
            raise HTTPException(status_code=404, detail="Database not found")
            
        # Delete
        mongo.execute_eval(f"db.inventory_databases.deleteOne({{'identity.db_unique_name': '{db_name}'}})")
        return {"status": f"Database {db_name} removed from inventory"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/status")
def get_system_status():
    """Get global system status (RUNNING/PAUSED)"""
    try:
        conf = mongo.execute_eval("db.system_config.findOne({key: 'global_status'})")
        # Default to RUNNING if not set
        status = conf.get('value', 'RUNNING') if conf else 'RUNNING'
        return {"status": status}
    except:
        return {"status": "RUNNING"}

@app.post("/api/system/status")
def set_system_status(item: dict):
    """Set global system status (RUNNING/PAUSED) - Controls Docker Lab containers"""
    import subprocess
    
    status = item.get("status", "RUNNING").upper()
    if status not in ["RUNNING", "PAUSED"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    # Containers to control (exclude frontend services)
    lab_containers = [
        "nexi-mongodb",
        "nexi-redis", 
        "nexi-ollama",
        "nexi-open-webui",
        "nexi-qdrant",
        "nexi-gw-milano",
        "nexi-gw-bratislava",
        "nexi-pg-milano-prod",
        "nexi-pg-milano-stg",
        "nexi-pg-milano-dev",
        "nexi-mongo-express",
        "nexi-pg-bratislava-prod",
        "nexi-pg-bratislava-dev",
        "nexi-gw-cairo",
        "nexi-oracle-cairo-primary",
        "nexi-oracle-cairo-replica"
    ]
    
    results = []
    action = "stop" if status == "PAUSED" else "start"
    
    try:
        for container in lab_containers:
            try:
                result = subprocess.run(
                    ["docker", action, container], 
                    capture_output=True, 
                    timeout=30,
                    text=True
                )
                success = result.returncode == 0
                results.append({
                    "container": container,
                    "action": action,
                    "success": success,
                    "message": result.stdout.strip() if success else result.stderr.strip()
                })
            except Exception as e:
                results.append({
                    "container": container,
                    "action": action,
                    "success": False,
                    "message": str(e)
                })
        
        # Update MongoDB status (if available)
        try:
            mongo.execute_eval(f"db.system_config.updateOne({{key: 'global_status'}}, {{$set: {{value: '{status}'}}}}, {{upsert: true}})")
        except:
            pass  # MongoDB might be stopped
        
        return {
            "status": status, 
            "containers_affected": len(lab_containers),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/raw/{collection}")
def get_raw_collection(collection: str):
    """Get raw JSON of a collection"""
    try:
        if collection not in ["inventory_databases", "monitoring_alerts", "system_config"]:
            raise HTTPException(status_code=400, detail="Invalid collection")
        
        data = mongo.execute_eval(f"db.{collection}.find().limit(100).toArray()")
        # Clean IDs
        for d in data:
            if "_id" in d: d["_id"] = str(d["_id"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/emails")
def get_emails():
    """List archived emails"""
    try:
        email_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../emails'))
        if not os.path.exists(email_dir): return []
        
        files = [f for f in os.listdir(email_dir) if f.endswith('.html')]
        files.sort(reverse=True) # Newest first
        return files
    except Exception as e:
        return []

@app.get("/api/emails/content")
def get_email_content(filename: str):
    """Get email content"""
    try:
        # Security check: filename only
        if "/" in filename or "\\" in filename: raise Exception("Invalid filename")
        
        email_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../emails'))
        path = os.path.join(email_dir, filename)
        
        if not os.path.exists(path): raise HTTPException(status_code=404, detail="File not found")
        
        with open(path, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# LLM MANAGEMENT ENDPOINTS
# =============================================================================

@app.get("/api/llm/models")
def get_llm_models():
    """List all available LLM models"""
    return {
        "models": LLM_MODELS,
        "current": current_llm_model,
        "default": DEFAULT_MODEL,
        "recommended": get_recommended_models()
    }

@app.get("/api/llm/current")
def get_current_model():
    """Get current LLM model in use"""
    global current_llm_model
    info = get_model_info(current_llm_model)
    return {
        "model": current_llm_model,
        "info": info
    }

@app.post("/api/llm/switch")
def switch_llm_model(req: ModelSwitchRequest):
    """Switch to a different LLM model"""
    global current_llm_model
    if req.model not in LLM_MODELS:
        raise HTTPException(status_code=400, detail=f"Model {req.model} not available. Use /api/llm/models to see options.")
    
    current_llm_model = req.model
    info = get_model_info(req.model)
    print(f"🔄 LLM Model switched to: {req.model}")
    return {
        "status": "switched",
        "model": req.model,
        "info": info
    }

@app.get("/api/gpu/status")
def get_gpu_status():
    """Get GPU status (VRAM usage)"""
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            return {
                "gpu_name": parts[0] if len(parts) > 0 else "Unknown",
                "memory_used_mb": int(parts[1]) if len(parts) > 1 else 0,
                "memory_total_mb": int(parts[2]) if len(parts) > 2 else 0,
                "utilization_pct": int(parts[3]) if len(parts) > 3 else 0
            }
        return {"error": "nvidia-smi failed"}
    except Exception as e:
        return {"error": str(e)}

# =============================================================================
# DEEP OBSERVABILITY ENDPOINTS
# =============================================================================

@app.get("/api/database/{db_name}/deep")
def get_deep_observability(db_name: str):
    """Get deep observability data for a specific database"""
    try:
        if not mongo: raise Exception("MongoProxy not initialized")
        
        db_info = mongo.execute_eval(f"db.inventory_databases.findOne({{'identity.db_unique_name': '{db_name}'}})")
        if not db_info:
            raise HTTPException(status_code=404, detail="Database not found")
        
        deep_obs = db_info.get('deep_observability', {})
        
        return {
            "db_name": db_name,
            "engine": db_info.get('identity', {}).get('engine', 'UNKNOWN'),
            "status": db_info.get('state', {}).get('status', 'UNKNOWN'),
            "deep_observability": deep_obs,
            "has_oracle_internals": 'oracle_internals' in deep_obs,
            "has_checkmk_metrics": 'external_metrics' in deep_obs and 'checkmk' in deep_obs.get('external_metrics', {}),
            "last_update": deep_obs.get('last_update', 'Never')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts/ai")
def get_alerts_with_ai_analysis():
    """Get alerts that have AI analysis attached"""
    try:
        if not mongo: raise Exception("MongoProxy not initialized")
        
        alerts = mongo.execute_eval("""
            db.monitoring_alerts.find({ai_analysis: {$exists: true}})
            .sort({timestamp: -1})
            .limit(20)
            .toArray()
        """)
        
        for a in alerts:
            if "_id" in a:
                a["_id"] = str(a["_id"])
        
        return alerts or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/status")
def get_agents_status():
    """Get status of all agents (checks for running Python processes)"""
    import subprocess
    
    agents = {
        "Scout": {"script": "Agents/Scout/main.py", "running": False},
        "CriticalAlert": {"script": "Agents/CriticalAlert/critical_alert.py", "running": False},
        "Watcher": {"script": "Agents/Watcher/main.py", "running": False},
        "ForensicAnalyzer": {"script": "Agents/Watcher/ai_analyzer.py", "running": False},
        "CheckMK_Bridge": {"script": "Agents/CheckMK_Bridge/main.py", "running": False},
        "Collector": {"script": "Agents/Collector/main.py", "running": False}
    }
    
    try:
        # Get list of running Python processes
        result = subprocess.run(
            ["wmic", "process", "where", "name='python.exe'", "get", "commandline"],
            capture_output=True, text=True, timeout=10
        )
        
        running_processes = result.stdout.lower()
        
        for name, info in agents.items():
            script_name = info["script"].lower().replace("/", "\\\\")
            if script_name in running_processes or info["script"].lower() in running_processes:
                agents[name]["running"] = True
                
    except Exception as e:
        print(f"Error checking agents: {e}")
    
    return {"agents": agents}

@app.post("/api/agents/start/{agent_name}")
def start_agent(agent_name: str):
    """Start a specific agent"""
    agent_scripts = {
        "scout": "Agents/Scout/main.py",
        "criticalalert": "Agents/CriticalAlert/critical_alert.py",
        "watcher": "Agents/Watcher/main.py",
        "forensicanalyzer": "Agents/Watcher/ai_analyzer.py",
        "checkmk_bridge": "Agents/CheckMK_Bridge/main.py",
        "collector": "Agents/Collector/main.py"
    }
    
    script = agent_scripts.get(agent_name.lower())
    if not script:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../', script))
        subprocess.Popen([sys.executable, script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
        return {"status": f"Agent {agent_name} started", "script": script}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/trigger/watcher")
def trigger_watcher_once():
    """Trigger Watcher agent for a single scan"""
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Agents/Watcher/main.py'))
        subprocess.Popen([sys.executable, script_path])
        return {"status": "Watcher triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/trigger/checkmk")
def trigger_checkmk_sync():
    """Trigger CheckMK Bridge for a single sync"""
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Agents/CheckMK_Bridge/main.py'))
        subprocess.Popen([sys.executable, script_path, "--once"])
        return {"status": "CheckMK sync triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/trigger/forensic")
def trigger_forensic_analysis():
    """Trigger Forensic AI Analyzer for a single run"""
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Agents/Watcher/ai_analyzer.py'))
        subprocess.Popen([sys.executable, script_path, "--once"])
        return {"status": "Forensic Analyzer triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rag/status")
def get_rag_status():
    """Get RAG pipeline status (Ollama + Qdrant)"""
    import requests
    
    status = {
        "ollama": {"connected": False, "models": []},
        "qdrant": {"connected": False, "collections": 0}
    }
    
    # Check Ollama
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            status["ollama"]["connected"] = True
            status["ollama"]["models"] = [m["name"] for m in resp.json().get("models", [])]
    except:
        pass
    
    # Check Qdrant
    try:
        resp = requests.get("http://localhost:6333/collections", timeout=5)
        if resp.status_code == 200:
            collections = resp.json().get("result", {}).get("collections", [])
            status["qdrant"]["connected"] = True
            status["qdrant"]["collections"] = len(collections)
    except:
        pass
    
    return status

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
