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
        Orchestrator <-->|Inference| Ollama[Local LLM (Ollama)]
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
| **[Agents](./Agents/README.md)** | 🤖 | **The Hands** | Autonomous workers that discover (`Scout`), monitor (`Collector`), and analyze (`Watcher`) database infrastructure. |
| **[Orchestrator](./Orchestrator/README.md)** | 🧠 | **The Brain** | The AI Core handling LLM interactions, RAG pipelines, and decision-making logic. |
| **[WebInterface](./WebInterface/README.md)** | 💻 | **The Face** | The user-facing dashboard (React) and the API server (FastAPI) enabling control and visibility. |
| **[MongoDB](./MongoDB/README.md)** | 💾 | **The Memory** | Central data store schemas, initialization scripts, and state management. |
| **[docker-lab](./docker-lab)** | 🐳 | **Simulation** | Sandbox environment with Oracle, Postgres, and other containers for safe testing. |
| **[scripts](./scripts)** | 🛠️ | **Tools** | Essential automation scripts for setup, cleanup, and maintenance `setup_v2.ps1`. |

---

## 🚀 Quick Start (Windows)

1.  **Start System**:
    ```powershell
    .\scripts\setup_v2.ps1
    ```
2.  **Access Dashboard**:
    Open [http://localhost:4002](http://localhost:4002)
3.  **Run Manual Discovery** (Optional):
    ```powershell
    python Agents/Scout/main.py --once
    ```

---

## 📚 Essential Reading

- **[Pipeline Architecture](docs/pipeline_explained.md)**: How raw data becomes insights.
- **[Data Ingestion Specs](docs/data_ingestion_specs.md)**: Details on WAL, RMAN, and ASM data collection.

---

> _"From Chaos to Order" - Built for Nexi by the Advanced Agentic Coding Team_
