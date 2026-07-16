# 🧠 AI Project Context

> Master reference for AI assistants. **Read this first.**

---

## 🎯 Quick Context

```yaml
Project: M-DN DBA AI
Purpose: AI-powered database monitoring and management CMDB
Version: V3 (Shadow Mode on V2 ports)
Stack: Python/FastAPI + React + MongoDB + Ollama LLM

# Critical Ports (ALWAYS use these)
Backend: 8000
Frontend: 4002
MongoDB: 28017
Langfuse: 3001

# Environment
Config File: .env.v2 (NOT .env)
Gateway Suffix: GATEWAY_SUFFIX=2
```

---

## 🏗️ Architecture Overview

```mermaid
flowchart TB
    subgraph User["👤 User"]
        Browser[Browser]
    end

    subgraph App["🖥️ Application"]
        FE[React :4002]
        BE[FastAPI :9000]
    end

    subgraph AI["🤖 AI"]
        Ollama[Ollama LLM]
        Qdrant[Qdrant Vector]
    end

    subgraph Data["💾 Data"]
        MongoDB[(MongoDB :28017)]
    end

    subgraph Agents["🔧 Agents"]
        Scout[Scout]
        Collector[Collector]
        CriticalAlert[CriticalAlert]
    end

    Browser --> FE --> BE
    BE --> MongoDB
    BE --> Ollama --> Qdrant
    Agents --> MongoDB
```

---

## 📂 Directory Map

```mermaid
flowchart LR
    subgraph L1["Layer 1: Directives"]
        Dir[directives/*.md]
    end

    subgraph L2["Layer 2: Orchestration"]
        BE[WebInterface/backend/]
        Orch[Orchestrator/]
    end

    subgraph L3["Layer 3: Execution"]
        Exec[execution/*.py]
        Agents[Agents/]
    end

    Dir --> BE
    BE --> Exec
    BE --> Agents
```

| Path | Layer | Purpose |
|------|-------|---------|
| `directives/` | L1 | SOPs (what to do) |
| `WebInterface/backend/` | L2 | API & routing |
| `Orchestrator/` | L2 | LLM + RAG |
| `execution/` | L3 | Deterministic scripts |
| `Agents/` | L3 | Background workers |

---

## ⚡ Key Commands

```powershell
# Start everything (zero-config)
.\scripts\setup_v2.ps1

# Stop and clean everything
.\scripts\cleanup_v2.ps1

# Run database discovery
python Agents/Scout/main.py --once

# Seed MongoDB collections
python execution/seed_mongodb.py
```

---

## 📊 MongoDB Collections

```mermaid
erDiagram
    inventory_databases {
        ObjectId _id
        object identity
        object state
        object business_service
    }

    monitoring_alerts {
        ObjectId _id
        string db_name
        string state
        boolean processed
        object ai_analysis
    }

    system_config {
        string key
        any value
        datetime updated_at
    }

    gateways {
        string _id
        object location
        object network
    }

    inventory_databases ||--o{ monitoring_alerts : generates
    gateways ||--o{ inventory_databases : reaches
```

| Collection | Purpose |
|------------|---------|
| `inventory_databases` | Discovered databases |
| `monitoring_alerts` | Active alerts |
| `system_config` | Agent intervals, global settings |
| `gateways` | SSH gateway info |
| `business_services` | Service-to-DB mapping |

---

## 🔧 When You Need To...

| Task | Action |
|------|--------|
| Fix a bug | Edit code → Test with `setup_v2.ps1` → Commit to v3 |
| Add feature | Update directive first → Then implement |
| Debug "error loading" | Check backend logs, verify ports |
| Reset everything | `cleanup_v2.ps1` → `setup_v2.ps1` |
| Push to personal repo | `git push personal v3:main` |

---

## ⚠️ Critical Constraints

1. **Always V2 Ports**: Backend `8000`, MongoDB `28017`, Frontend `4002`
2. **Environment File**: Use `.env.v2` (not `.env`)
3. **Gateway Suffix**: `GATEWAY_SUFFIX=2` for V2 containers
4. **Branch Strategy**: Develop on `v3`, sync to `v2`

---

## 🔗 Related Files

| Document | Description |
|----------|-------------|
| [README.md](../README.md) | Quick start |
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Technical architecture |
| [AGENTS.md](../AGENTS.md) | Agent documentation |
| [MANIFEST.md](../MANIFEST.md) | Port mappings |
| [ROADMAP_V3.md](../ROADMAP_V3.md) | Development roadmap |
