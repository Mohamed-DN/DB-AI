from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import os
import subprocess
import json
import sys
import re
import uvicorn
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment
# Load environment variables
# Prioritize .env.v2 for V2 Shadow Mode
env_v2_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env.v2'))
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env'))

if os.path.exists(env_v2_path):
    print(f"Loading config from {env_v2_path}")
    load_dotenv(env_v2_path, override=True)
elif os.path.exists(env_path):
    print(f"Loading config from {env_path}")
    load_dotenv(env_path)
else:
    print("Warning: No .env file found")

# Import MongoProxy
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from Orchestrator.src.mongo_proxy import MongoProxy
from Orchestrator.config.llm_config import (
    LLM_MODELS, DEFAULT_MODEL, FALLBACK_MODEL, OLLAMA_CONFIG,
    get_model_info, get_recommended_models, get_all_models
)

# Langfuse LLM Observability (optional - graceful fallback if not configured)
try:
    from langfuse import Langfuse
    LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://localhost:3001")
    LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
    
    if LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY:
        langfuse = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST
        )
        LANGFUSE_ENABLED = True
        print("[OK] Langfuse observability enabled")
    else:
        langfuse = None
        LANGFUSE_ENABLED = False
        print("[INFO] Langfuse keys not set, observability disabled")
except ImportError:
    langfuse = None
    LANGFUSE_ENABLED = False
    print("[INFO] Langfuse not installed, observability disabled")

app = FastAPI(title="Nexi AI CMDB", version="2.0.0", description="AI-Powered Database Management")

SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._/\-]+$")

def validate_identifier(value: str, label: str) -> str:
    if not value or not SAFE_IDENTIFIER_RE.match(value):
        raise HTTPException(status_code=400, detail=f"Invalid {label}")
    return value

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
    print("[OK] Backend connected to MongoProxy")
except Exception as e:
    print(f"[ERROR] Backend MongoProxy failed: {e}")
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
    """Get all databases enriched with Business Service info"""
    try:
        if not mongo: raise Exception("MongoProxy not initialized")
        
        # 1. Fetch Inventory
        dbs = mongo.execute_eval("db.inventory_databases.find({}, {'_id': 0}).toArray()") or []
        
        # 2. Fetch Business Services
        services = mongo.execute_eval("db.business_services.find({}, {'_id': 0}).toArray()") or []
        
        # 3. Create Lookup Map (DB Name -> Service Info)
        service_map = {}
        default_svc = None
        for svc in services:
            svc_info_obj = svc.get('service_info', svc)  # Support both flat and nested
            service_entry = {
                "name": svc_info_obj.get("name"),
                "snow_group": svc_info_obj.get("snow_group"),
                "reperibility": svc.get("contacts", {}).get("reperibilita_number"),
                "contacts": svc.get("contacts")
            }
            
            # technical_mapping can be a list of objects or a single object
            mappings = svc.get('technical_mapping', [])
            if isinstance(mappings, dict):
                mappings = [mappings]
            
            for mapping in mappings:
                if isinstance(mapping, dict):
                    db_name = mapping.get('db_unique_name')
                    if db_name == "ALL":
                        default_svc = service_entry
                    elif db_name:
                        service_map[db_name.upper()] = service_entry
                elif isinstance(mapping, str):
                    if mapping == "ALL":
                        default_svc = service_entry
                    else:
                        service_map[mapping.upper()] = service_entry
        
        # 4. Enrich DB objects
        for db in dbs:
            db_name = db.get('identity', {}).get('db_unique_name', '').upper()
            # Exact match ?
            svc_info = service_map.get(db_name)
            
            # Fallback to ALL if available
            if not svc_info and default_svc:
                svc_info = default_svc
                
            if svc_info:
                db['business_service'] = svc_info
        
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
        alerts = mongo.execute_eval("db.monitoring_alerts.find().sort({timestamp: -1}).limit(50).toArray()") or []
        
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

@app.get("/api/storage")
def get_all_storage():
    """Get all storage inventory items"""
    try:
        if not mongo: raise Exception("MongoProxy not initialized")
        storage = mongo.execute_eval("db.inventory_storage.find().toArray()") or []
        for s in storage:
            if "_id" in s:
                s["_id"] = str(s["_id"])
        return storage
    except Exception as e:
        print(f"Error fetching storage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/storage/{db_name}")
def get_storage_for_db(db_name: str):
    """Get storage inventory for a specific database"""
    try:
        if not mongo: raise Exception("MongoProxy not initialized")
        db_name = validate_identifier(db_name, "database")
        storage = mongo.execute_eval(f"db.inventory_storage.findOne({{db_ref: '{db_name}'}})")
        if not storage:
            raise HTTPException(status_code=404, detail=f"No storage found for {db_name}")
        if "_id" in storage:
            storage["_id"] = str(storage["_id"])
        return storage
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching storage for {db_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- HELPER FUNCTIONS ---
def connect_db(db_name, mode="sql"):
    """Validates DB and opens terminal"""
    try:
        db_name = validate_identifier(db_name, "database")
        if mode not in {"sql", "bash", "sysdba"}:
            raise HTTPException(status_code=400, detail="Invalid connection mode")
        # 1. Get DB info
        db_info = mongo.execute_eval(f"db.inventory_databases.findOne({{'identity.db_unique_name': '{db_name}'}})")
        if not db_info:
            return False, f"Database {db_name} not found"
            
        container = (
            db_info.get('connection', {}).get('container') or 
            db_info.get('identity', {}).get('db_name') or 
            db_info.get('identity', {}).get('host')
        )
        if not container:
             return False, "DEBUG_UNIQUE_ERROR: No container/host found for database"
             
        engine = db_info.get('identity', {}).get('engine', 'POSTGRES').upper()
        
        # 2. Open terminal
        if os.name == 'nt': # Windows
            if mode == 'bash':
                cmd = f'start cmd /k "docker exec -it {container} bash"'
            else: # sql
                if engine == 'ORACLE':
                    cmd = f'start cmd /k "docker exec -it {container} sqlplus sys/nexi2024 as sysdba"'
                elif engine == 'POSTGRES':
                    cmd = f'start cmd /k "docker exec -it {container} psql -U postgres"'
                else:
                    cmd = f'start cmd /k "docker exec -it {container} bash"'
            
            subprocess.Popen(cmd, shell=True)
            return True, "Terminal launched"
        return False, "Not running on Windows Server"
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return False, str(e)

# --- MISSING ENDPOINTS ---

@app.get("/api/raw/{collection_name}")
def get_raw_collection(collection_name: str):
    """Get raw collection data for Explorer"""
    try:
        if not mongo: raise Exception("MongoProxy not initialized")
        allowed = [
            "inventory_databases",
            "monitoring_alerts",
            "business_services",
            "system_config",
            "discovery_queue",
            "agent_runs",
            "baselines",
            "compliance_reports",
            "gateways",
            "rag_knowledge_base"
        ]
        if collection_name not in allowed:
             raise HTTPException(status_code=400, detail="Invalid collection")
        
        data = mongo.execute_eval(f"db.{collection_name}.find().limit(100).toArray()")
        for item in data:
            if "_id" in item:
                item["_id"] = str(item["_id"])
        return data
    except Exception as e:
        print(f"Error fetching raw collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# In-memory agent state with process tracking
AGENTS_STATE = {
    "scout": {"running": False, "process": None},
    "collector": {"running": False, "process": None},
    "watcher": {"running": False, "process": None},
    "criticalalert": {"running": False, "process": None},
    "forensicanalyzer": {"running": False, "process": None},
    "checkmk_bridge": {"running": False, "process": None}
}

# Map agent names to script paths
AGENT_SCRIPTS = {
    "scout": "../../Agents/Scout/main.py",
    "collector": "../../Agents/Collector/main.py",
    "watcher": "../../Agents/Watcher/main.py",
    "criticalalert": "../../Agents/CriticalAlert/main.py",
    "forensicanalyzer": "../../Agents/Watcher/ai_analyzer.py",
    "checkmk_bridge": "../../Agents/CheckMK_Bridge/main.py"
}

@app.get("/api/agents/status")
def get_agents_status():
    """Get status of background agents"""
    # Create clean status dict without process objects
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

@app.post("/api/agents/start/{agent_name}")
def start_agent_endpoint(agent_name: str):
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
             
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), script_rel_path))
        
        # Spawn process (continuous mode)
        proc = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
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

@app.post("/api/agents/stop/{agent_name}")
def stop_agent_endpoint(agent_name: str):
    agent_key = agent_name.lower()
    
    if agent_key not in AGENTS_STATE:
         raise HTTPException(status_code=404, detail="Agent not found")
         
    state = AGENTS_STATE[agent_key]
    
    if not state["running"] or not state["process"]:
        return {"status": "not_running", "agent": agent_name}
        
    try:
        # Terminate process
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


@app.post("/api/chat")
def chat_with_ai(request: ChatRequest):
    """Interact with Local Ollama - Multi-DB Expert with Action Capabilities"""
    import requests
    import json
    import re
    
    prompt = request.message
    
    # Get system context
    try:
        db_count = mongo.execute_eval("db.inventory_databases.countDocuments({})")
        active_alerts = mongo.execute_eval('db.monitoring_alerts.countDocuments({"state": "CRITICAL", "processed": false})')
        # Get list of databases
        dbs = mongo.execute_eval("db.inventory_databases.find({}, {'identity.db_unique_name': 1, 'identity.engine': 1, 'state.status': 1}).limit(20).toArray()")
        db_list = "\n".join([f"   - {d['identity']['db_unique_name']} ({d['identity']['engine']}) - {d['state']['status']}" for d in dbs]) if dbs else "No databases found"
    except:
        db_count = "Unknown"
        active_alerts = "Unknown"
        db_list = "Unable to fetch"
    
    system_prompt = f"""You are NEXI DBA, an EXPERT Database Administrator AI with 20+ years of experience.
You are a MULTI-DATABASE EXPERT specializing in:
- **Oracle** (19c, 21c, RAC, Data Guard, RMAN, ASM, AWR, PDBs, CDBs)
- **PostgreSQL** (15+, replication, extensions, pg_stat)
- **MySQL** (8.0+, InnoDB, replication, performance_schema)
- **DB2** (LUW, z/OS, HADR, backup/recovery)
- **Cassandra** (clusters, CQL, compaction, repair)
- **MongoDB** (replica sets, sharding, aggregation)

⚡ CRITICAL BEHAVIOR RULES:
1. **LANGUAGE**: ALWAYS respond in the SAME language as the user (Italian, English, etc.)
2. **BE DECISIVE**: Do NOT ask unnecessary questions. REASON through the problem, then EXECUTE or PROVIDE the solution.
3. **ACTION-ORIENTED**: When user asks to DO something, DO IT. Don't just explain.
4. **PROVIDE COMPLETE SOLUTIONS**: Give full SQL/commands, not partial examples.
5. **REASON STEP-BY-STEP**: For complex problems, think through the solution, then act.

📊 CURRENT SYSTEM STATE:
- Total Databases: {db_count}
- Critical Alerts: {active_alerts}
- Available Databases:
{db_list}

🔧 TOOLS AVAILABLE (output JSON to execute):

1. **run_query**: Execute SQL on a database
   {{"action": "run_query", "database": "DB_NAME", "sql": "SELECT ..."}}

2. **connect_terminal**: Open SQL terminal to database
   {{"action": "connect_terminal", "database": "DB_NAME", "mode": "sql|bash"}}

3. **send_email**: Send email notification
   {{"action": "send_email", "to": "email", "subject": "...", "body": "..."}}

4. **create_alert**: Create monitoring alert
   {{"action": "create_alert", "database": "DB_NAME", "type": "WARNING|CRITICAL", "message": "..."}}

5. **run_script**: Execute maintenance script
   {{"action": "run_script", "script": "rman_backup|dataguard_check|tablespace_check", "database": "DB_NAME"}}

📝 RESPONSE GUIDELINES:
- For Oracle: Use V$ views, DBA_* views, RMAN commands, Data Guard broker
- For PostgreSQL: Use pg_* catalog, pg_stat views, psql commands
- For MySQL: Use information_schema, performance_schema, SHOW commands
- For DB2: Use SYSCAT views, db2 commands, HADR status
- If user needs help with a specific database, check if it's in the list above

🎯 EXAMPLES OF GOOD RESPONSES:
User: "oracle pdb on cairo"
→ List the PDBs on NEXI-ORACLE-CAIRO-PRIMARY with:
```sql
SELECT pdb_name, status, open_mode FROM cdb_pdbs ORDER BY pdb_name;
```

User: "drop user in postgres"  
→ Provide immediate solution:
```sql
DROP USER IF EXISTS username;
-- OR with dependencies:
REASSIGN OWNED BY username TO postgres;
DROP OWNED BY username;
DROP USER username;
```

User: "we sai oracle"
→ Understand as "verifica/status Oracle" and provide:
```sql
SELECT instance_name, status, database_status, active_state FROM v$instance;
SELECT name, open_mode, database_role FROM v$database;
```

Remember: BE HELPFUL, BE DECISIVE, SOLVE THE PROBLEM!
"""
    
    try:
        global current_llm_model
        model_to_use = request.model if request.model else current_llm_model
        
        # Langfuse trace (optional)
        trace = None
        generation = None
        if LANGFUSE_ENABLED and langfuse:
            trace = langfuse.trace(
                name="chat_with_ai",
                user_id="nexi-dba-user",
                metadata={"db_count": str(db_count), "active_alerts": str(active_alerts)}
            )
            generation = trace.generation(
                name="ollama-generate",
                model=model_to_use,
                input=prompt,
                metadata={"system_prompt_length": len(system_prompt)}
            )
        
        # Call Ollama with enhanced prompt
        full_prompt = f"System: {system_prompt}\n\nUser: {prompt}\n\nAssistant (be decisive and action-oriented):"
        response = requests.post(f"{OLLAMA_CONFIG['base_url']}/api/generate", json={
            "model": model_to_use,
            "prompt": full_prompt,
            "stream": False,
            "options": {**OLLAMA_CONFIG.get("options", {}), "temperature": 0.7}
        }, timeout=OLLAMA_CONFIG.get("timeout", 120))
        
        reply = response.json().get("response", "")
        
        # End Langfuse generation
        if generation:
            generation.end(output=reply)
        
        # Check for JSON Action in reply
        clean_reply = reply.strip()
        
        # Try to extract and execute JSON actions
        json_match = re.search(r'\{[^{}]*"action"[^{}]*\}', clean_reply)
        if json_match:
            try:
                action_json = json.loads(json_match.group())
                action = action_json.get("action")
                
                if action == "send_email":
                    from Agents.CriticalAlert.main import EmailSender
                    sender = EmailSender()
                    to = action_json.get("to", "mohamed.d.n.2002@gmail.com")
                    subj = action_json.get("subject", "Nexi AI Alert")
                    body = action_json.get("body", "No content")
                    sender.send_alert(to, subj, body)
                    return f"✅ **Action Executed**: Email sent to {to}\n\n{reply}"
                
                elif action == "connect_terminal":
                    db_name = validate_identifier(action_json.get("database"), "database")
                    mode = action_json.get("mode", "sql")
                    # Trigger terminal connection
                    connect_db(db_name, mode)
                    return f"✅ **Action Executed**: Terminal opened for {db_name} ({mode})\n\n{reply}"
                
                elif action == "run_query":
                    db_name = validate_identifier(action_json.get("database"), "database")
                    sql = action_json.get("sql")
                    
                    # EXECUTE THE QUERY
                    try:
                        # Lookup database container info
                        db_info = mongo.execute_eval(f"db.inventory_databases.findOne({{'identity.db_unique_name': '{db_name}'}})")
                        if not db_info:
                            return f"⚠️ Database **{db_name}** not found in inventory.\n\n{reply}"
                        
                        container = db_info.get('identity', {}).get('db_name') or db_info.get('identity', {}).get('host')
                        engine = db_info.get('identity', {}).get('engine', 'POSTGRES').upper()
                        
                        # Build docker exec command
                        if engine == 'ORACLE':
                            exec_cmd = f'docker exec {container} sqlplus -s sys/nexi2024 as sysdba <<< "{sql}"'
                        elif engine == 'MYSQL':
                            exec_cmd = f'docker exec {container} mysql -u root -ppassword -e "{sql}"'
                        elif engine == 'POSTGRES':
                            exec_cmd = f'docker exec {container} psql -U postgres -c "{sql}"'
                        else:
                            return f"⚠️ Unsupported engine: {engine}\n\n{reply}"
                        
                        # Execute via subprocess
                        result = subprocess.run(exec_cmd, shell=True, capture_output=True, text=True, timeout=30)
                        output = result.stdout or result.stderr
                        
                        if result.returncode == 0:
                            return f"✅ **Query Executed on {db_name} ({engine})**:\n\n```sql\n{sql}\n```\n\n**Result:**\n```\n{output[:3000]}\n```"
                        else:
                            return f"⚠️ **Query Error on {db_name}**:\n\n```\n{output[:2000]}\n```\n\n{reply}"
                    except subprocess.TimeoutExpired:
                        return f"⚠️ Query timeout after 30 seconds.\n\n{reply}"
                    except Exception as exec_err:
                        return f"⚠️ Execution error: {exec_err}\n\n{reply}"
                
                elif action == "create_alert":
                    db_name = validate_identifier(action_json.get("database"), "database")
                    alert_type = action_json.get("type", "WARNING")
                    message = action_json.get("message")
                    mongo.insert_alert({
                        "type": "USER_ALERT",
                        "state": alert_type,
                        "db_unique_name": db_name,
                        "message": message
                    })
                    return f"✅ **Alert Created**: {alert_type} alert for {db_name}\n\n{reply}"
                    
            except json.JSONDecodeError:
                pass
            except Exception as e:
                return f"⚠️ Action failed: {e}\n\n{reply}"
        
        return reply

    except Exception as e:
        return f"❌ AI Brain Offline: {str(e)}"

@app.post("/api/action/scan")
def trigger_scan():
    """Trigger Scout Agent"""
    try:
        # Path to Scout
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Agents/Scout/main.py'))
        subprocess.Popen([sys.executable, script_path, "--once"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "Scout Agent Triggered via Async Subprocess"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/action/auto-discovery")
def trigger_auto_discovery():
    """Backwards-compatible alias for auto-discovery"""
    return trigger_scan()

@app.post("/api/action/check")
def trigger_check():
    """Trigger CriticalAlert Agent"""
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Agents/CriticalAlert/main.py'))
        email = os.getenv("ALERT_EMAIL") or os.getenv("SMTP_USER") or "admin@nexi.com"
        subprocess.Popen(
            [sys.executable, script_path, "--email", email, "--once"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"status": "CriticalAlert Agent Triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/action/collect")
def trigger_collect():
    """Trigger Collector Agent"""
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Agents/Collector/main.py'))
        subprocess.Popen([sys.executable, script_path, "--once"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "Collector Agent Triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
def get_config():
    """Get all agent intervals"""
    agents = ['scout', 'criticalalert', 'watcher', 'forensicanalyzer', 'checkmk_bridge', 'collector']
    defaults = {'scout': 60, 'criticalalert': 30, 'watcher': 10, 'forensicanalyzer': 30, 'checkmk_bridge': 60, 'collector': 30}
    
    config = {}
    try:
        if not mongo:
            raise Exception("MongoProxy not initialized")
        for agent in agents:
            doc = mongo.execute_eval(f"db.system_config.findOne({{key: '{agent}_interval'}})")
            config[f"{agent}_interval"] = doc.get('value', defaults[agent]) if doc else defaults[agent]
        return config
    except:
        return {f"{a}_interval": defaults[a] for a in agents}

@app.post("/api/config")
def update_config(cfg: dict):
    """Update agent intervals"""
    try:
        if not mongo:
            raise Exception("MongoProxy not initialized")
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

@app.post("/api/action/connect/{db_name:path}")
def connect_db(db_name: str, mode: str = "sql"):
    """Open a terminal connection to the DB. Mode: 'sql' or 'bash'. db_name can be CDB or CDB/PDB"""
    try:
        db_name = validate_identifier(db_name, "database")
        if mode not in {"sql", "bash", "sysdba"}:
            raise HTTPException(status_code=400, detail="Invalid connection mode")
        # Lookup database to get container host
        if not mongo: raise Exception("MongoProxy not initialized")
        
        # Check if this is a PDB connection (format: CDB_NAME/PDB_NAME)
        # Handle PDB paths (e.g., "ORCLCDB/ORCLPDB1")
        pdb_name = None
        if "/" in db_name:
            parent_name, pdb_name = db_name.split("/", 1)
            # Find parent database
            # mongo.execute_eval returns a dict or None
            # DEBUG
            print(f"DEBUG: Connecting to PDB {pdb_name} of {parent_name}")
            db_info = mongo.execute_eval(f"db.inventory_databases.findOne({{'identity.db_unique_name': '{parent_name}'}})")
        else:
            # DEBUG
            print(f"DEBUG: Connecting to DB {db_name}")
            db_info = mongo.execute_eval(f"db.inventory_databases.findOne({{'identity.db_unique_name': '{db_name}'}})")

        if not db_info:
            print(f"ERROR: Database not found: {db_name}")
            raise HTTPException(status_code=404, detail=f"Database not found: {db_name}")
            
        container = (
            db_info.get('connection', {}).get('container') or 
            db_info.get('identity', {}).get('db_name') or 
            db_info.get('identity', {}).get('host') or
            db_info.get('identity', {}).get('db_unique_name', '').lower()  # Fallback to lowercase unique name
        )
        if not container:
             raise HTTPException(status_code=404, detail="Container name not found for database")
            
        # Determine command based on mode
        engine = db_info.get('identity', {}).get('engine', 'POSTGRES').upper()
        conn_type = db_info.get('connection', {}).get('type', 'DOCKER')

        if hasattr(conn_type, 'upper') and conn_type.upper() == "REMOTE":
            # Remote Connection (VirtualBox)
            conn = db_info.get('connection', {})
            host = conn.get('host')
            port = conn.get('port', 1521)
            service = conn.get('service_name')
            user = 'c##aiauto'  # Always use AIAUTO as requested
            password = 'root'
            
            # If connecting to a PDB, use PDB name as service and local AIAUTO user
            if pdb_name:
                service = pdb_name
                user = 'aiauto'  # PDB user without C## prefix
            
            # Get gateway container name (default to maesdn-gateway for VirtualBox)
            gateway = db_info.get('identity', {}).get('gateway_ref', 'REMOTE_VBOX')
            # Use Cairo Oracle container as SQLPlus jump host (has SQLPlus installed)
            sqlplus_container = "nexi-oracle-cairo-primary"
            
            if mode == "bash":
                # Open bash shell on Cairo container
                cmd = f'start powershell -NoExit -Command "Write-Host \'Opening shell on Oracle Gateway ({sqlplus_container})...\' -ForegroundColor Cyan; docker exec -it {sqlplus_container} bash"'
            elif mode == "sysdba":
                # Connect as SYSDBA via TCP (requires password)
                # NOTE: Assuming password 'root' for SYS in VirtualBox Lab
                pdb_label = f" (PDB: {pdb_name})" if pdb_name else ""
                connect_str = f"sys/root@//{host}:{port}/{service} as sysdba"
                cmd = f'start powershell -NoExit -Command "Write-Host \'Connecting to Oracle {host}{pdb_label} as SYSDBA...\' -ForegroundColor Yellow; docker exec -it {sqlplus_container} sqlplus {connect_str}"'
            else:
                # Connect to VirtualBox Oracle using REAL SQLPlus from Cairo container
                pdb_label = f" (PDB: {pdb_name})" if pdb_name else ""
                # Use EZConnect format: user/pass@//host:port/service
                connect_str = f"{user}/{password}@//{host}:{port}/{service}"
                cmd = f'start powershell -NoExit -Command "Write-Host \'Connecting to Oracle {host}{pdb_label} as {user} via SQLPlus...\' -ForegroundColor Green; docker exec -it {sqlplus_container} sqlplus {connect_str}"'
            
        else:
            # Docker Container Connection - Direct exec into container
            # For PostgreSQL, use the container name as the host (Docker DNS)
            # The container variable already holds the correct container name
            db_port = db_info.get('configuration', {}).get('port', 5432)
            
            if mode == "bash":
                # Open bash shell on the database container directly
                cmd = f'start powershell -NoExit -Command "Write-Host \'Opening shell on {container}...\' -ForegroundColor Cyan; docker exec -it {container} /bin/bash"'
            elif mode == "sysdba":
                # Oracle SYSDBA mode - direct exec without credentials
                if engine == 'ORACLE':
                    cmd = f'start powershell -NoExit -Command "Write-Host \'Starting Oracle Console as SYSDBA...\' -ForegroundColor Yellow; docker exec -it {container} sqlplus / as sysdba"'
                else:
                    # PostgreSQL superuser mode
                    cmd = f'start powershell -NoExit -Command "Write-Host \'Connecting to PostgreSQL ({container}) as POSTGRES (superuser)...\' -ForegroundColor Yellow; docker exec -it {container} psql -U postgres"'
            else:
                # SQL Mode - Direct exec into container with aiauto user
                # SQL Mode - Direct exec into container
                if engine == 'ORACLE':
                    # Oracle Docker - Force SYSDBA as requested
                    cmd = f'start powershell -NoExit -Command "Write-Host \'Starting Oracle Console as SYSDBA (Enforced)...\'-ForegroundColor Yellow; docker exec -it {container} sqlplus / as sysdba"'
                else:
                    # PostgreSQL - direct exec into container with psql
                    # Connect locally inside the container (no network hop needed)
                    cmd = f'start powershell -NoExit -Command "Write-Host \'Connecting to PostgreSQL ({container}) as AIAUTO...\' -ForegroundColor Green; docker exec -e PGPASSWORD=root -it {container} psql -U aiauto -d postgres"'
        
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
        return {"status": status, "paused": status == "PAUSED"}
    except:
        return {"status": "RUNNING", "paused": False}

@app.post("/api/system/status")
def set_system_status(item: dict):
    """Set global system status (RUNNING/PAUSED) - Controls Docker Lab containers with Streaming Progress"""
    status = item.get("status", "RUNNING").upper()
    if status not in ["RUNNING", "PAUSED"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    # Containers to control - V2 names with suffix (exclude frontend services)
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
    
    import shutil
    import json
    import time
    
    docker_cmd = shutil.which("docker") or "/usr/local/bin/docker"
    action = "stop" if status == "PAUSED" else "start"

    def event_generator():
        # Update MongoDB global status first
        try:
            if mongo:
                 mongo.execute_eval(f"db.system_config.updateOne({{key: 'global_status'}}, {{$set: {{value: '{status}'}}}}, {{upsert: true}})")
        except:
            pass

        # Yield initial event
        yield json.dumps({"type": "start", "action": action, "total": len(lab_containers)}) + "\n"

        success_count = 0
        
        for container in lab_containers:
            try:
                # Notify starting action on container
                yield json.dumps({"type": "progress", "container": container, "status": "pending"}) + "\n"
                
                # Execute Docker command
                cmd = [docker_cmd, action, container]
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    timeout=30,
                    text=True
                )
                success = result.returncode == 0
                if success: success_count += 1
                
                # Notify completion of action
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
        
        # Yield final summary
        yield json.dumps({
            "type": "complete", 
            "status": status, 
            "success_count": success_count,
            "total": len(lab_containers)
        }) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

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

@app.delete("/api/emails/{filename}")
def delete_email(filename: str):
    """Delete a single email"""
    try:
        # Security check: filename only
        if "/" in filename or "\\" in filename: raise Exception("Invalid filename")
        
        email_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../emails'))
        path = os.path.join(email_dir, filename)
        
        if not os.path.exists(path): raise HTTPException(status_code=404, detail="File not found")
        
        os.remove(path)
        return {"status": "deleted", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/emails/all")
def delete_all_emails():
    """Delete all emails from the inbox"""
    try:
        email_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../emails'))
        if not os.path.exists(email_dir): return {"status": "no emails to delete", "count": 0}
        
        count = 0
        for f in os.listdir(email_dir):
            if f.endswith('.html'):
                os.remove(os.path.join(email_dir, f))
                count += 1
        
        return {"status": "deleted", "count": count}
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

@app.post("/api/agents/trigger/watcher")
def trigger_watcher_once():
    """Trigger Watcher agent for a single scan"""
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Agents/Watcher/main.py'))
        subprocess.Popen([sys.executable, script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "Watcher triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/trigger/checkmk")
def trigger_checkmk_sync():
    """Trigger CheckMK Bridge for a single sync"""
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Agents/CheckMK_Bridge/main.py'))
        subprocess.Popen([sys.executable, script_path, "--once"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "CheckMK sync triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/trigger/forensic")
def trigger_forensic_analysis():
    """Trigger Forensic AI Analyzer for a single run"""
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Agents/Watcher/ai_analyzer.py'))
        subprocess.Popen([sys.executable, script_path, "--once"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
    
    # Get config from env (set by setup script or defaults)
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    # Handle case where OLLAMA_HOST might be just hostname/IP without protocol/port if set differently
    # But for V2 script we use full URLs or ports. Let's rely on PORT env vars if HOST not full.
    if not ollama_host.startswith("http"):
         ollama_port = os.getenv("OLLAMA_PORT", "11434")
         ollama_host = f"http://localhost:{ollama_port}"

    qdrant_host = os.getenv("QDRANT_HOST", "http://localhost:6333")
    if not qdrant_host.startswith("http"):
         qdrant_port = os.getenv("QDRANT_PORT", "6333")
         qdrant_host = f"http://localhost:{qdrant_port}"
    
    # Check Ollama
    try:
        resp = requests.get(f"{ollama_host}/api/tags", timeout=5)
        if resp.status_code == 200:
            status["ollama"]["connected"] = True
            status["ollama"]["models"] = [m["name"] for m in resp.json().get("models", [])]
    except:
        pass
    
    # Check Qdrant
    try:
        resp = requests.get(f"{qdrant_host}/collections", timeout=5)
        if resp.status_code == 200:
            collections = resp.json().get("result", {}).get("collections", [])
            status["qdrant"]["connected"] = True
            status["qdrant"]["collections"] = len(collections)
    except:
        pass
    
    return status

# =============================================================================
# DATABASE METRICS ENDPOINT
# =============================================================================

@app.get("/api/metrics")
def get_database_metrics():
    """Get aggregated database metrics for the metrics dashboard"""
    try:
        if not mongo:
            raise Exception("MongoProxy not initialized")
        
        # Fetch inventory for connection counts and sizes
        dbs = mongo.execute_eval("db.inventory_databases.find({}, {'_id': 0}).toArray()") or []
        
        # Fetch recent alerts count
        alert_count = mongo.execute_eval("db.monitoring_alerts.countDocuments({status: 'pending'})") or 0
        
        # Aggregate metrics
        total_size_bytes = 0
        total_connections = 0
        pg_databases = []
        oracle_tablespaces = []
        connections_by_db = []
        
        for db in dbs:
            identity = db.get('identity', {})
            storage = db.get('storage', {})
            status = db.get('status', {})
            
            db_name = identity.get('db_unique_name', identity.get('db_name', 'Unknown'))
            engine = identity.get('engine', 'UNKNOWN').upper()
            
            # Get size
            size_bytes = 0
            if 'total_size_bytes' in storage:
                size_bytes = storage.get('total_size_bytes', 0)
            elif 'total_size' in storage:
                # Parse size string like "1.5 GB"
                size_str = storage.get('total_size', '0')
                try:
                    if 'GB' in str(size_str):
                        size_bytes = float(str(size_str).replace('GB', '').strip()) * 1024 * 1024 * 1024
                    elif 'MB' in str(size_str):
                        size_bytes = float(str(size_str).replace('MB', '').strip()) * 1024 * 1024
                    elif 'TB' in str(size_str):
                        size_bytes = float(str(size_str).replace('TB', '').strip()) * 1024 * 1024 * 1024 * 1024
                except:
                    pass
            total_size_bytes += size_bytes
            
            # Get connections
            active_conns = status.get('active_sessions', 0) or status.get('connections', 0) or 0
            idle_conns = status.get('idle_sessions', 0) or 0
            total_connections += active_conns + idle_conns
            
            connections_by_db.append({
                'name': db_name[:15],  # Truncate for display
                'active': active_conns,
                'idle': idle_conns,
                'engine': engine
            })
            
            # PostgreSQL specific
            if engine == 'POSTGRES':
                pg_databases.append({
                    'name': db_name,
                    'size_bytes': size_bytes,
                    'size_gb': round(size_bytes / (1024**3), 2) if size_bytes else 0,
                    'connections': active_conns + idle_conns
                })
            
            # Oracle tablespace info
            if engine == 'ORACLE':
                tablespaces = storage.get('tablespaces', [])
                for ts in tablespaces:
                    oracle_tablespaces.append({
                        'name': ts.get('name', 'UNKNOWN'),
                        'used_pct': ts.get('used_pct', 0),
                        'used_gb': ts.get('used_gb', 0),
                        'max_gb': ts.get('max_gb', 0)
                    })
        
        # Calculate mock performance metrics (would come from prometheus/exporter in real setup)
        import random
        buffer_hit = 95 + random.random() * 4.5
        tps = 1000 + random.randint(0, 500)
        avg_query_ms = 5 + random.random() * 15
        
        return {
            "summary": {
                "buffer_hit": round(buffer_hit, 1),
                "tps": tps,
                "storage_gb": round(total_size_bytes / (1024**3), 1),
                "total_connections": total_connections,
                "avg_query_ms": round(avg_query_ms, 1),
                "active_alerts": alert_count
            },
            "connections_by_db": sorted(connections_by_db, key=lambda x: x['active'], reverse=True)[:5],
            "pg_databases": pg_databases[:10],
            "oracle_tablespaces": oracle_tablespaces[:10],
            "database_count": len(dbs)
        }
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics/deep")
def get_deep_metrics():
    """Get deep dive metrics for advanced dashboard"""
    try:
        if not mongo:
            raise Exception("MongoProxy not initialized")
        
        # Fetch all data
        dbs = mongo.execute_eval("db.inventory_databases.find({}, {'_id': 0}).toArray()") or []
        alerts = mongo.execute_eval("db.monitoring_alerts.find().sort({timestamp: -1}).limit(10).toArray()") or []
        
        # Build tablespace data
        tablespaces = []
        asm_diskgroups = []
        pg_databases = []
        resources = []
        
        for db in dbs:
            identity = db.get('identity', {})
            storage = db.get('storage', {})
            status = db.get('status', {})
            engine = identity.get('engine', 'UNKNOWN').upper()
            db_name = identity.get('db_unique_name', '')
            
            if engine == 'ORACLE':
                # Tablespaces
                for ts in storage.get('tablespaces', []):
                    tablespaces.append({
                        'name': ts.get('name', 'UNKNOWN'),
                        'used': ts.get('used_pct', 0),
                        'usedGB': ts.get('used_gb', 0),
                        'maxGB': ts.get('max_gb', ts.get('used_gb', 0) * 1.2),  # Estimate max
                        'growthPerDay': round(ts.get('used_gb', 0) * 0.01, 2)  # Estimate 1% daily growth
                    })
                
                # ASM (if available)
                for asm in storage.get('asm_diskgroups', []):
                    asm_diskgroups.append({
                        'name': asm.get('name', '+DATA'),
                        'used': asm.get('used_pct', 0),
                        'total': asm.get('total_gb', 0),
                        'free': asm.get('free_gb', 0)
                    })
                
                # Resources
                if status.get('processes_pct'):
                    resources.append({
                        'name': 'Processes',
                        'current': status.get('processes_current', 0),
                        'limit': status.get('processes_limit', 300),
                        'pct': status.get('processes_pct', 0)
                    })
                if status.get('sessions_pct'):
                    resources.append({
                        'name': 'Sessions',
                        'current': status.get('sessions_current', 0),
                        'limit': status.get('sessions_limit', 500),
                        'pct': status.get('sessions_pct', 0)
                    })
            
            elif engine == 'POSTGRES':
                size_bytes = storage.get('total_size_bytes', 0)
                pg_databases.append({
                    'name': db_name,
                    'size_gb': round(size_bytes / (1024**3), 2) if size_bytes else 0,
                    'xid_age': status.get('xid_age', 100000000),
                    'xid_pct': round(status.get('xid_age', 100000000) / 2000000000 * 100, 2)
                })
        
        # Add mock data if empty (for demo)
        if not tablespaces:
            tablespaces = [
                {'name': 'USERS', 'used': 78, 'usedGB': 156, 'maxGB': 200, 'growthPerDay': 0.5},
                {'name': 'SYSTEM', 'used': 92, 'usedGB': 46, 'maxGB': 50, 'growthPerDay': 0.1},
                {'name': 'SYSAUX', 'used': 67, 'usedGB': 33.5, 'maxGB': 50, 'growthPerDay': 0.2},
            ]
        
        if not asm_diskgroups:
            asm_diskgroups = [
                {'name': '+DATA', 'used': 72, 'total': 500, 'free': 140},
                {'name': '+RECO', 'used': 45, 'total': 200, 'free': 110},
            ]
        
        if not resources:
            resources = [
                {'name': 'Processes', 'current': 245, 'limit': 300, 'pct': 82},
                {'name': 'Sessions', 'current': 380, 'limit': 500, 'pct': 76},
            ]
        
        return {
            "tablespaces": tablespaces,
            "asm_diskgroups": asm_diskgroups,
            "pg_databases": pg_databases,
            "resources": resources,
            "active_alerts": [
                {"severity": a.get('severity', 'warning'), "message": a.get('message', '')}
                for a in alerts[:5]
            ]
        }
    except Exception as e:
        print(f"Error fetching deep metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
