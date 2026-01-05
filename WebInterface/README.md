# 🌐 WebInterface - Nexi DBA AI Dashboard

Dashboard web per monitoraggio e controllo del sistema.

## 📋 Struttura

```
WebInterface/
├── frontend/
│   ├── index.html          # UI principale
│   ├── app.js              # Logica JavaScript
│   └── style.css           # Stili CSS
├── backend/
│   └── main.py             # API FastAPI
└── run_dashboard.ps1       # Script avvio completo
```

---

## 🚀 Avvio

```powershell
.\WebInterface\run_dashboard.ps1
```

Questo avvia:
- **Frontend** su `http://localhost:3000`
- **Backend** su `http://localhost:8000`
- Agenti **Scout** e **CriticalAlert**

---

## 🖥️ Frontend

### Sezioni

| Sezione | Descrizione |
|---------|-------------|
| **Dashboard** | Overview statistiche (DB totali, alert, healthy) |
| **Inventory** | Tabella database con status, engine, host, port |
| **Alerts** | Storico alert con severità e timestamp |
| **AI Chat** | Assistente conversazionale con selezione modello |
| **Mailbox** | Archivio email inviate (visualizzatore HTML) |
| **Explorer** | JSON tree + Graph view per collezioni MongoDB |
| **Agents** | Controllo agenti, RAG status, quick actions |
| **Settings** | Configurazione intervalli per tutti gli agenti |

### Tecnologie

- **HTML5** + **CSS3** (no framework)
- **JavaScript** vanilla (no React/Vue)
- **Font Awesome** per icone
- **Canvas API** per graph visualization

---

## ⚡ Backend API

### Endpoints Principali

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/api/inventory` | GET | Lista database |
| `/api/alerts` | GET | Ultimi 50 alert |
| `/api/chat` | POST | Chat con AI |
| `/api/config` | GET/POST | Configurazione intervalli |

### Endpoints Agenti

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/api/agents/status` | GET | Status tutti gli agenti |
| `/api/agents/start/{name}` | POST | Esegui agente (singola esecuzione) |
| `/api/agents/trigger/checkmk` | POST | Sync CheckMK |
| `/api/agents/trigger/forensic` | POST | Analisi AI |
| `/api/agents/trigger/watcher` | POST | Avvia Watcher |

### Endpoints Deep Observability

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/api/database/{name}/deep` | GET | Metriche deep per database |
| `/api/alerts/ai` | GET | Alert con analisi AI |
| `/api/rag/status` | GET | Status Ollama + Qdrant |

### Endpoints Azioni

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/api/action/scan` | POST | Trigger Scout |
| `/api/action/check` | POST | Trigger CriticalAlert |
| `/api/action/clear_alerts` | POST | Pulisci coda alert |
| `/api/action/connect/{db_name}` | POST | Apri SQL/Bash console |

### Endpoints Sistema

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/api/system/status` | GET/POST | Stato globale (RUNNING/PAUSED) |
| `/api/gpu/status` | GET | Status GPU (nvidia-smi) |
| `/api/llm/models` | GET | Modelli LLM disponibili |
| `/api/llm/switch` | POST | Cambia modello LLM |

---

## 🎨 Styling

### Tema

Il dashboard usa un tema **dark mode** con:
- Background: `#0a0a0a`
- Card: `#1a1a1a`
- Accent: `#4ade80` (verde)
- Danger: `#ef4444` (rosso)

### Componenti Custom

- **Modal popup** per conferme
- **Process Log** per output agenti
- **JSON Tree** per visualizzazione dati
- **Canvas Graph** per relazioni

---

## 🔧 Personalizzazione

### Aggiungere una nuova sezione

1. **HTML** (`index.html`):
   ```html
   <!-- Nav button -->
   <button class="nav-pill" onclick="showSection('mySection')">
       <i class="fa-solid fa-icon"></i> My Section
   </button>
   
   <!-- Section content -->
   <section id="mySection" class="page-section">
       <!-- Content here -->
   </section>
   ```

2. **JavaScript** (`app.js`):
   ```javascript
   // In showSection()
   const titles = {
       // ...
       'mySection': 'My Section Title'
   };
   
   // Load handler
   if (id === 'mySection') loadMySection();
   ```

### Aggiungere un endpoint API

1. **Backend** (`backend/main.py`):
   ```python
   @app.get("/api/myendpoint")
   def my_endpoint():
       return {"data": "value"}
   ```

2. **Frontend** (`app.js`):
   ```javascript
   async function loadMyData() {
       const data = await fetch(`${API_URL}/myendpoint`).then(r => r.json());
       // Use data
   }
   ```

---

## 📝 Note

- Il frontend serve file statici via `python -m http.server`
- Il backend usa **uvicorn** per ASGI
- CORS è abilitato per `*` (sviluppo)
- Per produzione, configurare CORS appropriatamente
