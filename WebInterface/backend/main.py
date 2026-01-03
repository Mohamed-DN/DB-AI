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

app = FastAPI(title="Nexi AI CMDB", version="1.0.0")

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
    
    system_prompt = f"""You are the Nexi DBA AI Assistant.
    Current System State:
    - Total Databases Managed: {db_count}
    - Active Critical Alerts: {active_alerts}
    
    TOOLS AVAILABLE:
    1. send_email: Send an email to a user. Format: {{"action": "send_email", "to": "email_address", "subject": "subject", "body": "message_body"}}
    
    INSTRUCTIONS:
    - If the user asks to send an email, output ONLY the JSON object for the tool. Do not add extra text.
    - If no action is needed, just reply as a helpful assistant.
    - If the user provided an email address previously, use it. Default to 'mohamed.d.n.2002@gmail.com' if not specified.
    """
    
    try:
        # Call Ollama
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "llama3:8b",
            "prompt": f"System: {system_prompt}\nUser: {prompt}\nAssistant:",
            "stream": False
        })
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
