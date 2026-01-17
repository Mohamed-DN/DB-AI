"""
LLM Router - AI Chat, model management, and RAG status endpoints (Async with Motor)
"""
import os
import re
import json
import subprocess
import requests
from fastapi import APIRouter, HTTPException
from ..services.mongo_service import get_mongo_service
from ..dependencies import validate_identifier, SAFE_IDENTIFIER_RE
from ..config import (
    LLM_MODELS, DEFAULT_MODEL, FALLBACK_MODEL, OLLAMA_CONFIG,
    get_model_info, get_recommended_models, get_all_models,
    LANGFUSE_ENABLED, langfuse
)
from ..models import ChatRequest, ModelSwitchRequest

router = APIRouter()

# Mutable state for current model
_current_model = DEFAULT_MODEL


def get_current_model_name():
    global _current_model
    return _current_model


def set_current_model_name(model: str):
    global _current_model
    _current_model = model


# =============================================================================
# LLM Configuration Endpoints
# =============================================================================

@router.get("/llm/config")
async def get_llm_config():
    """Get available LLM models and current selection"""
    ollama_models = []
    ollama_status = "Unknown"
    
    try:
        response = requests.get(f"{OLLAMA_CONFIG['base_url']}/api/tags", timeout=5)
        if response.status_code == 200:
            ollama_status = "Connected"
            for model in response.json().get('models', []):
                ollama_models.append({
                    "name": model.get('name'),
                    "size": model.get('size'),
                    "modified": model.get('modified_at')
                })
    except:
        ollama_status = "Disconnected"
    
    return {
        "current_model": get_current_model_name(),
        "default_model": DEFAULT_MODEL,
        "fallback_model": FALLBACK_MODEL,
        "available_models": LLM_MODELS,
        "recommended_models": get_recommended_models(),
        "ollama_status": ollama_status,
        "ollama_models": ollama_models,
        "langfuse_enabled": LANGFUSE_ENABLED
    }


@router.get("/llm/models")
async def get_llm_models():
    """List all available LLM models"""
    return {
        "models": LLM_MODELS,
        "current": get_current_model_name(),
        "default": DEFAULT_MODEL,
        "recommended": get_recommended_models()
    }


@router.get("/llm/current")
async def get_current_model():
    """Get current LLM model in use"""
    model = get_current_model_name()
    info = get_model_info(model)
    return {"model": model, "info": info}


@router.post("/llm/switch")
async def switch_llm_model(req: ModelSwitchRequest):
    """Switch to a different LLM model"""
    if req.model not in LLM_MODELS:
        raise HTTPException(
            status_code=400, 
            detail=f"Model {req.model} not available. Use /api/llm/models to see options."
        )
    
    set_current_model_name(req.model)
    info = get_model_info(req.model)
    print(f"🔄 LLM Model switched to: {req.model}")
    return {"status": "switched", "model": req.model, "info": info}


@router.get("/gpu/status")
async def get_gpu_status():
    """Get GPU status (VRAM usage)"""
    try:
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


@router.get("/rag/status")
async def get_rag_status():
    """Get RAG pipeline status (Ollama + Qdrant)"""
    status = {"ollama": {"status": "Unknown"}, "qdrant": {"status": "Unknown"}}
    
    # Check Ollama - Try common ports
    ollama_urls = [
        OLLAMA_CONFIG.get('base_url'),
        "http://localhost:11434",
        "http://localhost:12434", # V2 Port
        "http://nexi-ollama2:11434" # Internal Docker DNS
    ]
    # Filter nones and duplicates
    ollama_urls = list(dict.fromkeys([u for u in ollama_urls if u]))
    
    ollama_connected = False
    for url in ollama_urls:
        try:
            # Short timeout to fast fail
            response = requests.get(f"{url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = [m.get('name') for m in response.json().get('models', [])]
                status["ollama"] = {
                    "status": "Connected",
                    "url": url,
                    "models": models,
                    "current_model": get_current_model_name()
                }
                ollama_connected = True
                break
        except:
            continue
            
    if not ollama_connected:
         status["ollama"] = {"status": "Disconnected", "checked_urls": ollama_urls}
    
    # Check Qdrant
    qdrant_host = os.getenv("QDRANT_HOST", "http://localhost:7333")
    qdrant_urls = [
        qdrant_host,
        "http://localhost:6333",
        "http://localhost:7333", # V2 Port
        "http://nexi-qdrant2:6333"
    ]
    qdrant_urls = list(dict.fromkeys([u for u in qdrant_urls if u]))

    qdrant_connected = False
    for url in qdrant_urls:
        try:
            response = requests.get(f"{url}/collections", timeout=2)
            if response.status_code == 200:
                collections = response.json().get('result', {}).get('collections', [])
                status["qdrant"] = {
                    "status": "Connected",
                    "url": url,
                    "collections": [c.get('name') for c in collections]
                }
                qdrant_connected = True
                break
        except:
            continue

    if not qdrant_connected:
        status["qdrant"] = {"status": "Disconnected", "checked_urls": qdrant_urls}
    
    return status


# =============================================================================
# AI Chat Endpoint
# =============================================================================

@router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    """Interact with Local Ollama - Multi-DB Expert with Action Capabilities"""
    prompt = request.message
    mongo = get_mongo_service()
    
    # Get system context
    try:
        db_count = await mongo.count_databases()
        active_alerts = await mongo.count_critical_alerts()
        dbs = await mongo.get_inventory()
        dbs = dbs[:20]  # Limit to 20
        db_list = "\n".join([
            f"   - {d.get('identity', {}).get('db_unique_name', 'UNKNOWN')} "
            f"({d.get('identity', {}).get('engine', 'UNKNOWN')}) - "
            f"{d.get('state', {}).get('status', 'UNKNOWN')}"
            for d in dbs
        ]) if dbs else "No databases found"
    except:
        db_count = "Unknown"
        active_alerts = "Unknown"
        db_list = "Unable to fetch"
    
    system_prompt = f"""You are NEXI DBA, an EXPERT Database Administrator AI with 20+ years of experience.
You are a MULTI-DATABASE EXPERT specializing in:
- **Oracle** (19c, 12c, 21c, RAC, Data Guard, RMAN, ASM, AWR, PDBs, CDBs)
- **PostgreSQL** (8+, 15+, replication, extensions, pg_stat)
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

📝 RESPONSE GUIDELINES:
- For Oracle: Use V$ views, DBA_* views, RMAN commands, Data Guard broker
- For PostgreSQL: Use pg_* catalog, pg_stat views, psql commands
- For MySQL: Use information_schema, performance_schema, SHOW commands
- If user needs help with a specific database, check if it's in the list above

Remember: BE HELPFUL, BE DECISIVE, SOLVE THE PROBLEM!
"""
    
    try:
        model_to_use = request.model if request.model else get_current_model_name()
        
        # Langfuse trace (optional)
        trace = None
        generation = None
        if LANGFUSE_ENABLED and langfuse:
            try:
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
            except Exception as e:
                print(f"[WARN] Langfuse tracing failed: {e}")
                trace = None
                generation = None
        
        # Call Ollama
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
                    try:
                        from api_agents.workers.CriticalAlert.critical_alert_agent import EmailSender
                        sender = EmailSender()
                        to = action_json.get("to", "admin@nexi.com")
                        subj = action_json.get("subject", "Nexi AI Alert")
                        body = action_json.get("body", "No content")
                        sender.send_alert(to, subj, body)
                        return f"✅ **Action Executed**: Email sent to {to}\n\n{reply}"
                    except Exception as e:
                        return f"⚠️ Email action failed: {e}\n\n{reply}"
                
                elif action == "connect_terminal":
                    db_name = validate_identifier(action_json.get("database"), "database")
                    mode = action_json.get("mode", "sql")
                    from .connection import connect_db
                    await connect_db(db_name, mode)
                    return f"✅ **Action Executed**: Terminal opened for {db_name} ({mode})\n\n{reply}"
                
                elif action == "run_query":
                    return await _execute_query(action_json, mongo, reply)
                
                elif action == "create_alert":
                    db_name = validate_identifier(action_json.get("database"), "database")
                    alert_type = action_json.get("type", "WARNING")
                    message = action_json.get("message")
                    await mongo.insert_alert({
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


async def _execute_query(action_json: dict, mongo, reply: str) -> str:
    """Execute a SQL query action with security validation."""
    db_name = validate_identifier(action_json.get("database"), "database")
    sql = action_json.get("sql", "").strip()
    
    # SECURITY: SQL Whitelist Validation
    SAFE_SQL_PATTERNS = [
        r"^\s*SELECT\s+",
        r"^\s*SHOW\s+",
        r"^\s*DESCRIBE\s+",
        r"^\s*DESC\s+",
        r"^\s*EXPLAIN\s+",
        r"^\s*\\d",
    ]
    
    sql_upper = sql.upper()
    is_safe = any(re.match(pattern, sql_upper, re.IGNORECASE) for pattern in SAFE_SQL_PATTERNS)
    
    DANGEROUS_KEYWORDS = ['DROP', 'DELETE', 'TRUNCATE', 'INSERT', 'UPDATE', 
                          'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'EXEC', 
                          'EXECUTE', '--', ';', 'UNION']
    has_dangerous = any(kw in sql_upper for kw in DANGEROUS_KEYWORDS if kw not in ['--'])
    
    if not is_safe or has_dangerous:
        return "⛔ **Security Block**: Only SELECT/SHOW/DESCRIBE queries allowed via AI chat.\n\nFor write operations, use the SQL terminal directly."
    
    try:
        db_info = await mongo.get_database(db_name)
        if not db_info:
            return f"⚠️ Database **{db_name}** not found in inventory.\n\n{reply}"
        
        container = db_info.get('identity', {}).get('db_name') or db_info.get('identity', {}).get('host')
        if not container or not SAFE_IDENTIFIER_RE.match(container):
            return f"⚠️ Invalid container name.\n\n{reply}"
        
        engine = db_info.get('identity', {}).get('engine', 'POSTGRES').upper()
        
        db_password = os.getenv("DB_ADMIN_PASSWORD", "")
        if not db_password:
            return f"⚠️ Database password not configured. Set DB_ADMIN_PASSWORD env var.\n\n{reply}"
        
        if engine == 'ORACLE':
            exec_cmd = ["docker", "exec", "-i", container, "sqlplus", "-s", f"sys/{db_password}", "as", "sysdba"]
        elif engine == 'MYSQL':
            exec_cmd = ["docker", "exec", "-i", container, "mysql", "-u", "root", f"-p{db_password}", "-e", sql]
        elif engine == 'POSTGRES':
            exec_cmd = ["docker", "exec", "-i", "-e", f"PGPASSWORD={db_password}", container, "psql", "-U", "postgres", "-c", sql]
        else:
            return f"⚠️ Unsupported engine: {engine}\n\n{reply}"
        
        if engine == 'ORACLE':
            result = subprocess.run(exec_cmd, input=sql, capture_output=True, text=True, timeout=30)
        else:
            result = subprocess.run(exec_cmd, capture_output=True, text=True, timeout=30)
        
        output = result.stdout or result.stderr
        
        if result.returncode == 0:
            return f"✅ **Query Executed on {db_name} ({engine})**:\n\n```sql\n{sql}\n```\n\n**Result:**\n```\n{output[:3000]}\n```"
        else:
            return f"⚠️ **Query Error on {db_name}**:\n\n```\n{output[:2000]}\n```\n\n{reply}"
    
    except subprocess.TimeoutExpired:
        return f"⚠️ Query timeout after 30 seconds.\n\n{reply}"
    except Exception as exec_err:
        return f"⚠️ Execution error: {exec_err}\n\n{reply}"
