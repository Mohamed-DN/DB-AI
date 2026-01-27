
import os
import time
import json
import random
import requests
from pymongo import MongoClient
from datetime import datetime

# --- CONFIGURAZIONE (Non toccare nulla se sei in locale) ---
# Updated default to match the Lab environment (Port 28017, Auth) if env var not set
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:nexi2024@localhost:28017/?authSource=admin")
DB_NAME = "nexi_dba_ai_prod"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = "deepseek-r1:8b"  # O il modello che hai installato

# --- PARTE 1: INSEMINAZIONE DEL CERVELLO (SI ESEGUE DA SOLO) ---
def initialize_mongo_brain(db):
    print("🧠 [SYSTEM] Verifica integrità neurale su MongoDB...")
    
    # 1. IL PROMPT (L'Anima dell'AI)
    system_prompt = {
        "role_id": "antigravity_core",
        "content": """
        SEI ANTIGRAVITY. IL TUO SCOPO È MANTENERE IL SISTEMA ONLINE.
        INPUT: Metriche JSON (CPU, RAM).
        LOGICA:
        - Se CPU > 80% o RAM > 85%: SITUAZIONE CRITICA.
        - Se CRITICO: Scegli uno script dalla lista strumenti per risolvere.
        - Se STABILE: Rispondi "monitor".
        OUTPUT: JSON PURO {"action": "nome_script_o_monitor", "reason": "spiegazione breve"}
        """
    }
    db.system_prompts.update_one({"role_id": "antigravity_core"}, {"$set": system_prompt}, upsert=True)

    # 2. GLI STRUMENTI (I Muscoli - Codice Python salvato nel DB)
    scripts = [
        {
            "name": "clear_cache",
            "code": "def run():\n    print('🧹 [FIX] Cache Redis svuotata. Memoria liberata di 4GB.')\n    return 'SUCCESS'"
        },
        {
            "name": "scale_up",
            "code": "def run():\n    print('🚀 [FIX] Kubernetes: Aggiunti 2 Pods al cluster.')\n    return 'SCALED'"
        },
        {
            "name": "emergency_restart",
            "code": "def run():\n    print('🔄 [FIX] Riavvio forzato del servizio Gateway in corso...')\n    return 'RESTARTED'"
        }
    ]
    
    for s in scripts:
        db.system_scripts.update_one({"name": s["name"]}, {"$set": s}, upsert=True)
    
    print("✅ [SYSTEM] Cervello e Strumenti sincronizzati su Mongo.")

# --- PARTE 2: IL MOTORE RALPH (LOOP OPERATIVO) ---
def get_ai_decision(db, metrics):
    prompt_doc = db.system_prompts.find_one({"role_id": "antigravity_core"})
    
    # Validation
    if not prompt_doc:
        print("❌ Prompt non trovato! Rieseguire inizializzazione.")
        return {"action": "monitor", "reason": "System Error"}
        
    tools_doc = list(db.system_scripts.find({}, {"name": 1}))
    tool_names = [t["name"] for t in tools_doc]
    
    full_prompt = f"{prompt_doc['content']}\n\nMETRICHE: {metrics}\nSTRUMENTI: {tool_names}\nRISPONDI SOLO JSON."
    
    try:
        # Tenta connessione a Ollama/Deepseek
        resp = requests.post(OLLAMA_URL, json={"model": MODEL_NAME, "prompt": full_prompt, "stream": False}, timeout=15)
        raw_reply = resp.json().get("response", "")
        # Estrazione JSON (se il modello chiacchiera)
        import re
        match = re.search(r'\{.*\}', raw_reply, re.DOTALL)
        if match: 
            return json.loads(match.group())
        else:
            print(f"⚠️ AI non ha risposto con JSON valido: {raw_reply[:50]}...")
            if metrics["cpu"] > 80: return {"action": "scale_up", "reason": "Fallback: Parse Error"}
            return {"action": "monitor", "reason": "Fallback: Parse Error"}
            
    except Exception as e:
        print(f"⚠️ Errore AI: {e}")
        # FALLBACK DI EMERGENZA (Se Ollama è spento, simula l'intelligenza per non crashare)
        if metrics["cpu"] > 80: return {"action": "scale_up", "reason": "Fallback: CPU Critica"}
        return {"action": "monitor", "reason": "Fallback: Sistema stabile"}

def execute_remedy(db, script_name):
    if script_name == "monitor": return
    
    script = db.system_scripts.find_one({"name": script_name})
    if script:
        print(f"⚙️ [RALPH] Scaricamento ed esecuzione script: {script_name}")
        # Esecuzione dinamica del codice scaricato dal DB
        try:
            exec(script["code"], globals())
            run() # Chiama la funzione run() dello script scaricato
        except Exception as e:
            print(f"❌ Errore esecuzione script: {e}")
    else:
        print(f"❌ Script {script_name} non trovato nel DB!")

def main_loop():
    print(f"🔌 Connessione a MongoDB: {MONGO_URI}")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    # 1. Setup Iniziale (Centralizzazione)
    initialize_mongo_brain(db)
    
    print("\n🚀 ANTIGRAVITY LOOP ATTIVO. PREMERE CTRL+C PER FERMARE.\n")
    
    try:
        while True:
            # SIMULAZIONE METRICHE (In prod leggi da Prometheus)
            cpu = random.randint(40, 95)
            ram = random.randint(30, 90)
            metrics = {"cpu": cpu, "ram": ram}
            
            print(f"📊 [METRICS] CPU: {cpu}% | RAM: {ram}%")
            
            # RALPH LOOP
            # R + A + L (Retrieval + Analysis + Logic)
            decision = get_ai_decision(db, metrics)
            print(f"🤖 [AI] Decisione: {decision.get('action', 'UNKNOWN').upper()} ({decision.get('reason')})")
            
            # P + H (Planning + Healing)
            if decision.get("action") != "monitor":
                execute_remedy(db, decision.get("action"))
                print("✨ [SYSTEM] Sistema stabilizzato.")
            
            print("-" * 40)
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n🛑 Loop arrestato dall'utente.")

if __name__ == "__main__":
    main_loop()
