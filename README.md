# Nexi DBA AI (CMDB V3)

> **Status**: Active Development (Shadow Mode on V2)
> **Goal**: AI-powered Autonomous Database Administration & CMDB

## 🧠 System Architecture

```mermaid
graph TD
    %% Users & Entry
    User((User)) -->|HTTP/Browsing| Frontend[Frontend Dashboard :4002]
    
    %% Web Layer
    subgraph "Web Interface Layer"
        Frontend -->|REST API| Backend[FastAPI Backend :9000]
    end
    
    %% Data Layer
    subgraph "Data Persistence"
        Backend <-->|Read/Write| MongoDB[(MongoDB :28017)]
        Agents <-->|Write Metrics| MongoDB
        Orchestrator <-->|Context Caching| MongoDB
    end
    
    %% Agent Layer
    subgraph "Autonomous Agents"
        Agents{Agents Manager}
        Agents -->|Discovery| Scout[Scout Agent]
        Agents -->|Monitoring| Collector[Collector Agent]
        Agents -->|Analysis| Watcher[Watcher Agent]
    end
    
    %% Target Infrastructure
    subgraph "Infrastructure"
        Scout -.->|Scan| Docker[Docker Containers]
        Collector -.->|Query| Docker
    end
    
    %% Intelligence Layer
    subgraph "AI Core (Orchestrator)"
        Backend <-->|Query| Orchestrator[AI Orchestrator]
        Orchestrator <-->|RAG| Qdrant[(Qdrant Vector DB)]
        Orchestrator <-->|Inference| Ollama["Local LLM (Ollama)"]
    end

    %% Class Definitions for Styling
    classDef web fill:#1f77b4,stroke:#fff,stroke-width:2px,color:#fff;
    classDef db fill:#ff7f0e,stroke:#fff,stroke-width:2px,color:#fff;
    classDef agent fill:#2ca02c,stroke:#fff,stroke-width:2px,color:#fff;
    classDef ai fill:#9467bd,stroke:#fff,stroke-width:2px,color:#fff;
    
    class Frontend,Backend web;
    class MongoDB,Qdrant,Docker db;
    class Agents,Scout,Collector,Watcher agent;
    class Orchestrator,Ollama ai;
```

## 🗺️ Navigation & Directory Structure

Click on the module name to view detailed documentation and diagrams.

| Module | Icon | Role | Description |
|--------|:----:|------|-------------|
| **[api_agents](./api_agents/README.md)** | 🤖 | **Backend & Agents** | Unified backend layer with FastAPI Gateway and Autonomous Workers (`Scout`, `Collector`, `Watcher`). |
| **[orchestrator](./orchestrator/README.md)** | 🧠 | **The Brain** | The AI Core handling LLM interactions, RAG pipelines, and decision-making logic. |
| **[web](./web/README.md)** | 💻 | **The Face** | The user-facing dashboard (`web/dashboard`) and legacy interfaces. |
| **[mongo](./mongo/README.md)** | 💾 | **The Memory** | Central data store schemas, scripts, and seeds. |
| **[ops](./ops/README.md)** | 🛠️ | **Operations** | Infrastructure tools, Docker Lab (`ops/docker-lab`), and Scripts (`ops/scripts`). |
| **[llm](./llm/README.md)** | 🗣️ | **Intelligence** | Configuration and clients for Large Language Models. |

---

## 🎮 System Control

### 1. Requirements
- **Docker Desktop** (running)
- **Python 3.10+**
- **PowerShell** (Admin recommended)

### 2. Commands (Ops)
All scripts are located in `ops/scripts/`.

| Action | Command | Description |
|--------|---------|-------------|
| **🚀 START** | `.\ops\scripts\setup_v2.ps1` | Starts the full stack (Containers, API, Frontend). |
| **🛑 STOP** | `.\ops\scripts\cleanup_v2.ps1` | Stops all containers and kills python processes. |
| **🧹 CLEAN** | `docker system prune -f` | **Warning**: Removes all stopped containers (Use with caution). |

---

## 📚 Essential Reading

- **[System Architecture](docs/architecture/system_architecture.md)**: High-level design and component interaction.
- **[Agents Overview](docs/architecture/agents_overview.md)**: Details on the autonomous workers.
- **[Qdrant Basics](docs/references/qdrant_basics.md)**: Understanding the Vector DB.
- **[Audit & Roadmap](docs/audit/ROADMAP_MIGLIORAMENTO_E_AUDIT_TECNICO.md)**: Technical audit and future improvements.
- **[Project Tasks](docs/TASKS.md)**: Current development checklist and status.

---

> _"From Chaos to Order" - Built for Nexi by the Advanced Agentic Coding Team_
