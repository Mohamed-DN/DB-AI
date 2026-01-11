# 🤖 Nexi DBA AI

> AI-Powered Database Management Platform | CMDB + Monitoring + LLM Chat

[![Version](https://img.shields.io/badge/version-3.0-blue.svg)](https://github.com/Mohamed-DN/DB-AI)
[![License](https://img.shields.io/badge/license-Internal-red.svg)]()
[![Stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20React%20%7C%20MongoDB-green.svg)]()

---

## 🎯 Overview

**Nexi DBA AI** is an intelligent database operations platform that:
- 🔍 **Auto-discovers** databases in Docker environments
- 📊 **Monitors** health, metrics, and logs in real-time
- 🚨 **Alerts** when issues arise with AI-powered analysis
- 💬 **Provides AI chat** for natural language database queries

---

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph Frontend["🖥️ Frontend (React)"]
        UI[Dashboard UI]
        Chat[AI Chat Panel]
        Alerts[Alerts Panel]
    end

    subgraph Backend["⚙️ Backend (FastAPI)"]
        API[REST API]
        Orchestrator[Orchestrator]
    end

    subgraph Agents["🤖 Agents"]
        Scout[Scout<br/>Discovery]
        Collector[Collector<br/>Metrics]
        Watcher[Watcher<br/>Logs]
        CriticalAlert[CriticalAlert<br/>Alerting]
    end

    subgraph Infrastructure["🏢 Infrastructure"]
        MongoDB[(MongoDB<br/>CMDB)]
        Ollama[Ollama<br/>LLM]
        Qdrant[(Qdrant<br/>VectorDB)]
        Langfuse[Langfuse<br/>Observability]
    end

    subgraph Databases["🗄️ Managed Databases"]
        PG[PostgreSQL]
        Oracle[Oracle]
        MySQL[MySQL]
    end

    UI --> API
    Chat --> API
    Alerts --> API
    
    API --> MongoDB
    API --> Orchestrator
    Orchestrator --> Ollama
    Orchestrator --> Qdrant
    
    Scout --> MongoDB
    Scout --> Databases
    Collector --> MongoDB
    Collector --> Databases
    Watcher --> MongoDB
    CriticalAlert --> MongoDB
    
    API -.-> Langfuse
```

---

## 📂 Project Structure

```
Nexi_DB_AI/
├── 📁 Agents/                 # Background workers
│   ├── Scout/                 # Database discovery
│   ├── Collector/             # Metrics collection
│   ├── Watcher/               # Log monitoring
│   └── CriticalAlert/         # Alerting
│
├── 📁 WebInterface/
│   ├── backend/               # FastAPI API
│   └── frontend-react/        # React Dashboard
│
├── 📁 Orchestrator/           # LLM + RAG pipeline
├── 📁 execution/              # Deterministic scripts
├── 📁 directives/             # AI SOPs
├── 📁 docker-lab/             # Docker infrastructure
│
├── 📄 ARCHITECTURE.md         # Technical details
├── 📄 AGENTS.md               # Agent documentation
├── 📄 MANIFEST.md             # Port mappings
└── 📄 ROADMAP_V3.md           # Development roadmap
```

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- Python 3.11+
- Node.js 18+

### One-Command Setup
```powershell
# Clone the repository
git clone https://github.com/Mohamed-DN/DB-AI.git
cd DB-AI

# Copy environment template
cp .env.example .env.v2

# Start everything (zero-config)
.\scripts\setup_v2.ps1
```

### Access Points
| Service | URL |
|---------|-----|
| 🖥️ Dashboard | http://localhost:4002 |
| 📡 API Docs | http://localhost:9000/docs |
| 🗄️ MongoDB UI | http://localhost:9081 |
| 📊 Langfuse | http://localhost:3001 |

---

## 🔄 3-Layer Architecture

```mermaid
flowchart LR
    subgraph L1["Layer 1: DIRECTIVES"]
        D1[database_discovery.md]
        D2[alert_processing.md]
        D3[metric_collection.md]
    end

    subgraph L2["Layer 2: ORCHESTRATION"]
        O1[AI Assistant]
        O2[Backend API]
    end

    subgraph L3["Layer 3: EXECUTION"]
        E1[discover_docker_databases.py]
        E2[seed_mongodb.py]
        E3[connect_database.py]
    end

    L1 --> L2
    L2 --> L3

    style L1 fill:#e1f5fe
    style L2 fill:#fff3e0
    style L3 fill:#e8f5e9
```

| Layer | Purpose | Location |
|-------|---------|----------|
| **Directives** | What to do (SOPs) | `directives/*.md` |
| **Orchestration** | Decision making | `WebInterface/backend/` |
| **Execution** | How to do it | `execution/*.py`, `Agents/` |

---

## 🗺️ Roadmap

```mermaid
gantt
    title Nexi DBA AI - Development Roadmap
    dateFormat  YYYY-MM
    
    section Phase 1 - Foundation ✅
    Zero-Config Setup           :done, 2024-01, 2024-02
    Auto-Discovery              :done, 2024-02, 2024-03
    AI Chat Integration         :done, 2024-03, 2024-04
    
    section Phase 2 - Observability ✅
    Langfuse Integration        :done, 2024-04, 2024-05
    MongoDB Seeding             :done, 2024-05, 2024-05
    Documentation Rewrite       :done, 2024-05, 2024-06
    
    section Phase 3 - Hardening
    Backend Modularization      :active, 2024-06, 2024-08
    Security Improvements       :2024-07, 2024-09
    Grafana Dashboards          :2024-08, 2024-10
    
    section Phase 4 - Enterprise
    Multi-tenant Support        :2024-10, 2025-01
    RBAC & SSO                  :2024-11, 2025-02
    Performance Optimization    :2025-01, 2025-03
```

### Current Status

| Category | Status | Details |
|----------|--------|---------|
| 🟢 **Core** | Complete | Discovery, Monitoring, Alerting |
| 🟢 **AI Chat** | Complete | Multi-DB expert with actions |
| 🟢 **Observability** | Complete | Langfuse LLM tracing |
| 🟡 **Security** | In Progress | Auth, input validation |
| ⚪ **Enterprise** | Planned | Multi-tenant, RBAC |

---

## 🤖 Agents

```mermaid
flowchart LR
    subgraph Discovery
        Scout[🔍 Scout]
    end
    
    subgraph Monitoring
        Collector[📊 Collector]
        Watcher[👁️ Watcher]
    end
    
    subgraph Alerting
        CA[🚨 CriticalAlert]
    end
    
    Scout -->|discovers| DB[(Databases)]
    Collector -->|collects from| DB
    Watcher -->|watches logs of| DB
    CA -->|checks availability of| DB
    
    Scout --> MongoDB[(MongoDB)]
    Collector --> MongoDB
    Watcher --> MongoDB
    CA --> MongoDB
```

| Agent | Purpose | Trigger |
|-------|---------|---------|
| **Scout** | Auto-discovery | `POST /api/auto-discovery` |
| **Collector** | Metrics | `POST /api/action/collect` |
| **Watcher** | Log monitoring | Background |
| **CriticalAlert** | Availability | `POST /api/action/check` |

---

## 🔧 Configuration

### Port Mappings (V2)

| Service | Port |
|---------|------|
| Backend API | 9000 |
| Frontend UI | 4002 |
| MongoDB | 28017 |
| Mongo Express | 9081 |
| Ollama LLM | 12434 |
| Langfuse | 3001 |

### Environment Variables

See [.env.example](.env.example) for full list.

Key variables:
```bash
MONGODB_PORT=28017
BACKEND_PORT=9000
OLLAMA_PORT=12434
LANGFUSE_PUBLIC_KEY=pk-lf-...
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Technical architecture |
| [AGENTS.md](AGENTS.md) | Agent documentation |
| [MANIFEST.md](MANIFEST.md) | Port mappings |
| [ROADMAP_V3.md](ROADMAP_V3.md) | Development roadmap |
| [FOR_AI/PROJECT_CONTEXT.md](FOR_AI/PROJECT_CONTEXT.md) | AI assistant context |

---

## 🛠️ Commands

```powershell
# Start everything
.\scripts\setup_v2.ps1

# Stop and clean
.\scripts\cleanup_v2.ps1

# Run discovery manually
python Agents/Scout/main.py --once

# Seed MongoDB
python execution/seed_mongodb.py
```

---

## 📄 License

Internal use only - Nexi Group

---

<p align="center">
  Made with ❤️ by the DBA AI Team
</p>
