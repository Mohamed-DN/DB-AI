from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import os
import subprocess
import json
import sys
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment
load_dotenv()

app = FastAPI(title="Nexi AI CMDB", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:nexi2024@127.0.0.1:27017/?authSource=admin")
client = MongoClient(MONGO_URI)
db = client["nexi_cmdb"]
inventory_col = db["inventory_databases"]
alerts_col = db["monitoring_alerts"]

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
        dbs = list(inventory_col.find({}, {"_id": 0})) # Exclude ID for valid JSON
        return dbs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
def get_alerts():
    """Get recent alerts"""
    try:
        alerts = list(alerts_col.find().sort("timestamp", -1).limit(50))
        for a in alerts:
            a["_id"] = str(a["_id"]) # Convert ObjectId
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat_with_ai(request: ChatRequest):
    """Interact with Local Ollama"""
    import requests
    
    prompt = request.message
    
    # Context Enhancement (RAG-lite)
    # We fetch random context from DB state to give LLM awareness
    stats = {
        "db_count": inventory_col.count_documents({}),
        "active_alerts": alerts_col.count_documents({"state": "CRITICAL", "processed": False})
    }
    
    system_prompt = f"""You are the Nexi DBA AI Assistant.
    Current System State:
    - Total Databases Managed: {stats['db_count']}
    - Active Critical Alerts: {stats['active_alerts']}
    
    You have the ability to analyze issues and suggest solutions.
    """
    
    try:
        # Call Ollama
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "llama3:8b",
            "prompt": f"System: {system_prompt}\nUser: {prompt}\nAssistant:",
            "stream": False
        })
        return response.json().get("response", "Error from Ollama")
    except Exception as e:
        return f"AI Brain Offline: {str(e)}"

@app.post("/api/action/scan")
def trigger_scan():
    """Trigger Scout Agent"""
    try:
        # Path to Scout
        # Assuming we are in backend dir, go up
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Agents/Scout/main.py'))
        subprocess.Popen([sys.executable, script_path])
        return {"status": "Scout Agent Triggered via Async Subprocess"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/action/check")
def trigger_check():
    """Trigger CriticalAlert Agent"""
    try:
        # Path to CriticalAlert
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Agents/CriticalAlert/main.py'))
        # Need to pass args if required, or let it load from env
        # CriticalAlert needs --email if running via main block? 
        # Check main.py... it requires --email unless we modify it.
        # I'll pass a default email here or read from env
        email = os.getenv("SMTP_USER", "admin@nexi.com")
        subprocess.Popen([sys.executable, script_path, "--email", email, "--once"])
        return {"status": "CriticalAlert Agent Triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
