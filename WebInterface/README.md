# 🖥️ WebInterface

> Frontend (React) and Backend (FastAPI) for the dashboard.

This directory contains the user-facing components of the Nexi DBA AI system. It is split into a modern React frontend and a Python FastAPI backend.

---

## 🏗️ Component Architecture

```mermaid
flowchart TB
    subgraph Frontend["🖥️ Frontend (React :4002)"]
        App[App.tsx]
        subgraph Components["Components"]
            Inventory[InventoryTable]
            Alerts[AlertsPanel]
            Agents[AgentsPanel]
            Chat[ChatPanel]
            Explorer[ExplorerPanel]
        end
        subgraph Hooks["React Query"]
            useInventory[useInventory]
            useAlerts[useAlerts]
            useAgents[useAgents]
        end
    end

    subgraph Backend["⚙️ Backend (FastAPI :9000)"]
        API[main.py]
        subgraph Endpoints["API Endpoints"]
        E1[/api/inventory]
        E2[/api/alerts]
        E3[/api/agents]
        E4[/api/chat]
        E5[/api/auto-discovery]
        end
        MongoProxy[MongoProxy]
    end

    subgraph External["🔌 External"]
        MongoDB[(MongoDB)]
        Ollama[Ollama LLM]
        Langfuse[Langfuse]
    end

    App --> Components
    Components --> Hooks
    Hooks --> API
    API --> Endpoints
    Endpoints --> MongoProxy --> MongoDB
    E4 --> Ollama
    API -.-> Langfuse
```

---

## 📂 Directory Contents

| Directory/File | Description | Status |
|----------------|-------------|--------|
| **`backend/`** | **FastAPI Backend**. The API server providing data to the frontend and handling tool execution. | ✅ Active |
| **`frontend-react/`** | **React Dashboard**. The modern V2/V3 user interface built with Vite and TypeScript. | ✅ Active |
| **`frontend/`** | **Legacy UI**. Old vanilla JS/HTML dashboard. Kept for reference or emergency fallback. | ⚠️ Legacy |
| **`run_dashboard.ps1`** | Powershell script to quickly launch the frontend and backend locally. | ✅ Active |

## 📁 Structure

```
WebInterface/
├── backend/
│   ├── main.py              # FastAPI app (~1000 lines)
│   └── requirements.txt
│
├── frontend-react/          # Modern UI
│   ├── src/
│   ├── package.json
│   └── vite.config.v2.ts
│
└── frontend/                # Legacy UI
    ├── index.html
    ├── app.js
    └── style.css
```

---

## 📋 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/inventory` | GET | List all databases |
| `/api/alerts` | GET | List pending alerts |
| `/api/agents/status` | GET | Agent status |
| `/api/agents/{name}/start` | POST | Start agent |
| `/api/auto-discovery` | POST | Trigger Scout |
| `/api/chat` | POST | AI chat |
| `/api/config` | GET/POST | System config |
| `/api/system/status` | GET/POST | Pause/Resume |

Full docs: `http://localhost:9000/docs`

---

## 🛠️ Commands

```powershell
# Backend
cd WebInterface/backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 9000

# Frontend
cd WebInterface/frontend-react
npm install
npm run dev:v2

# Or use setup script
.\scripts\setup_v2.ps1
```

---

## 🔗 Related

- [ARCHITECTURE.md](../ARCHITECTURE.md) - System design
- [directives/ai_chat.md](../directives/ai_chat.md) - Chat directive
