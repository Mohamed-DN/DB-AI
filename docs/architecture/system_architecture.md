# 🏗️ Architecture

> Technical architecture of the Nexi DBA AI platform.

---

## 🎯 AI Context

```yaml
Purpose: AI-powered CMDB with auto-discovery, monitoring, and LLM chat
Pattern: 3-Layer Architecture (Directives → Orchestration → Execution)
Stack: Python/FastAPI + React + MongoDB + Ollama LLM
Ports: Backend 9000, Frontend 4002, MongoDB 28017
```

---

## 🔄 3-Layer Architecture

```mermaid
flowchart TB
    subgraph L1["📜 Layer 1: DIRECTIVES"]
        direction LR
        D1[database_discovery.md]
        D2[alert_processing.md]
        D3[metric_collection.md]
        D4[ai_chat.md]
    end

    subgraph L2["🧠 Layer 2: ORCHESTRATION"]
        direction LR
        AI[AI Assistant<br/>Decision Making]
        API[Backend API<br/>Routing]
    end

    subgraph L3["⚡ Layer 3: EXECUTION"]
        direction LR
        E1[seed_mongodb.py]
        E2[discover_docker.py]
        E3[Agents/Scout]
        E4[Agents/Collector]
    end

    L1 --> L2
    L2 --> L3

    style L1 fill:#e3f2fd,stroke:#1976d2
    style L2 fill:#fff3e0,stroke:#f57c00
    style L3 fill:#e8f5e9,stroke:#388e3c
```

### Why This Works

| Layer | Responsibility | Example |
|-------|---------------|---------|
| **Directives** | WHAT to do | "Discover databases in Docker" |
| **Orchestration** | WHICH script to run | AI decides to call Scout |
| **Execution** | HOW to do it | `Scout/main.py` runs discovery |

---

## 🏢 System Architecture

```mermaid
flowchart TB
    subgraph Client["👤 Client"]
        Browser[Web Browser]
    end

    subgraph Frontend["🖥️ Frontend :4002"]
        React[React Dashboard]
    end

    subgraph Backend["⚙️ Backend :9000"]
        FastAPI[FastAPI]
        MongoProxy[MongoProxy]
    end

    subgraph Observability["📊 Observability"]
        Langfuse[Langfuse :3001]
    end

    subgraph AI["🤖 AI Layer"]
        Ollama[Ollama LLM :12434]
        Qdrant[Qdrant Vector :7333]
    end

    subgraph Data["💾 Data Layer"]
        MongoDB[(MongoDB :28017)]
    end

    subgraph Agents["🤖 Agents"]
        Scout[Scout]
        Collector[Collector]
        Watcher[Watcher]
        CriticalAlert[CriticalAlert]
    end

    subgraph Managed["🗄️ Managed DBs"]
        PG[(PostgreSQL)]
        Oracle[(Oracle)]
    end

    Browser --> React
    React --> FastAPI
    FastAPI --> MongoProxy --> MongoDB
    FastAPI --> Ollama
    FastAPI -.-> Langfuse
    Ollama --> Qdrant

    Agents --> MongoDB
    Agents --> Managed
```

---

## 📊 Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant A as Agent
    participant M as MongoDB
    participant L as LLM

    Note over U,L: Discovery Flow
    U->>F: Click "Scan"
    F->>B: POST /api/auto-discovery
    B->>A: Start Scout --once
    A->>M: Insert to inventory_databases
    A->>B: Done
    B->>F: 200 OK
    F->>U: Show new databases

    Note over U,L: Chat Flow
    U->>F: "Show PostgreSQL DBs"
    F->>B: POST /api/chat
    B->>M: Get context
    B->>L: Generate response
    L->>B: Response
    B->>F: AI Message
    F->>U: Display
```

---

## 📁 Directory Structure

```mermaid
flowchart LR
    subgraph Root["📦 Project Root"]
        direction TB
        Agents["Agents/<br/>🤖 Background workers"]
        Web["WebInterface/<br/>🖥️ Frontend + Backend"]
        Orch["Orchestrator/<br/>🧠 LLM + RAG"]
        Exec["execution/<br/>⚡ Scripts"]
        Dir["directives/<br/>📜 SOPs"]
        Docker["docker-lab/<br/>🐳 Infrastructure"]
    end

    Agents --> Scout & Collector & Watcher
    Web --> Backend & Frontend
    Orch --> LLM & RAG
```

---

## 🔌 Integration Points

| Component | Protocol | Port | Purpose |
|-----------|----------|------|---------|
| Frontend → Backend | HTTP/REST | 9000 | API calls |
| Backend → MongoDB | MongoDB | 28017 | Data storage |
| Backend → Ollama | HTTP | 12434 | LLM inference |
| Backend → Langfuse | HTTP | 3001 | Observability |
| Agents → MongoDB | MongoDB | 28017 | Results storage |

---

## 🔗 Related

- [README.md](README.md) - Quick start
- [AGENTS.md](AGENTS.md) - Agent documentation
- [MANIFEST.md](MANIFEST.md) - Port mappings

---

## 🔮 Future Architecture Vision

The platform is evolving towards a distributed, high-availability architecture with **3 Gateways** and **Redis-based Queues**.

```mermaid
flowchart TB
    subgraph DataSources["📊 Data Sources"]
        CheckMK[CheckMK Monitoring]
        OEM[Oracle Enterprise Manager]
        DB[Direct SQL Access]
        Machine[OS Metrics]
    end

    subgraph Gateways["🌐 Distributed Gateways"]
        direction LR
        GW1[Gateway 01<br/>+ Redis Queue]
        GW2[Gateway 02<br/>+ Redis Queue]
        GW3[Gateway 03<br/>+ Redis Queue]
    end

    subgraph Core["🧠 Central Core"]
        MongoDB[(MongoDB Cluster)]
        AI[AI Orchestrator]
    end

    %% Connections
    CheckMK & OEM & DB & Machine --> GW1 & GW2 & GW3
    GW1 & GW2 & GW3 <-->|Async Queue| MongoDB
    GW1 & GW2 & GW3 <-->|Context| AI

    %% Styling
    style Gateways fill:#e1f5fe,stroke:#01579b
    style Core fill:#fff3e0,stroke:#e65100
    style DataSources fill:#f3e5f5,stroke:#4a148c
```

### Key Changes
1. **Redundancy**: Moving from 2 to **3 Gateways** to ensure zero downtime.
2. **Asynchronous Processing**: **Redis Queues** on each gateway decouple data ingestion from processing.
3. **Unified Ingestion**: All 4 data sources (CheckMK, OEM, DB, Machine) flow through the same gateway layer.

