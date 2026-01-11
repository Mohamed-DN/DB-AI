# 🖥️ WebInterface

> Frontend (React) and Backend (FastAPI) for the dashboard.

---

## 🎯 AI Context

```yaml
Purpose: User-facing dashboard and API layer
Frontend: React + TypeScript + Vite (:4002)
Backend: FastAPI + Python (:9000)
Main Files:
  - backend/main.py (~1000 lines)
  - frontend-react/src/App.tsx
```

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

Full docs: http://localhost:9000/docs

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

## 📁 Structure

```
WebInterface/
├── backend/
│   ├── main.py              # FastAPI app (~1000 lines)
│   └── requirements.txt
│
└── frontend-react/
    ├── src/
    │   ├── App.tsx          # Main component
    │   ├── components/      # UI components
    │   │   ├── Inventory/
    │   │   ├── Alerts/
    │   │   ├── Agents/
    │   │   ├── Chat/
    │   │   └── Explorer/
    │   ├── hooks/           # React Query
    │   └── services/        # API client
    ├── package.json
    └── vite.config.v2.ts
```

---

## 🔗 Related

- [ARCHITECTURE.md](../ARCHITECTURE.md) - System design
- [directives/ai_chat.md](../directives/ai_chat.md) - Chat directive
