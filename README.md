# M-DN DBA AI (CMDB V3)

> **Status**: Active Development (Shadow Mode on V2)
> **Goal**: AI-powered Autonomous Database Administration & CMDB

## 🏗️ Architecture

> **[See Full Architecture Documentation](docs/ARCHITECTURE.md)**

The system follows a **3-Layer Architecture**:
1. **Directives**: Rules & SOPs.
2. **Orchestration**: AI Decision Making.
3. **Execution**: Python Agents.

[View Architecture Diagram](docs/ARCHITECTURE.md#architecture-diagram)

## 🗺️ Navigation & Directory Structure

Click on the module name to view detailed documentation and diagrams.

| Module | Icon | Role | Description |
|--------|:----:|------|-------------|
| **[api_agents](./api_agents/README.md)** | 🤖 | **Backend & Agents** | Unified backend layer with FastAPI Gateway and Autonomous Workers (`scout`, `collector`, `watcher`). |
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

## 🔮 Future Architecture & Data Sources

### Data Sources
The system integrates 4 main data streams for holistic monitoring:
1. **CheckMK**: Infrastructure status and legacy alerts.
2. **OEM (Oracle Enterprise Manager)**: Deep database performance metrics.
3. **Database**: Direct SQL queries for internal state and logs.
4. **Machine**: OS-level metrics (CPU, RAM, Disk I/O).

### Infrastructure Evolution
We are moving towards a distributed gateway architecture:
- **Current State**: 2 Primary Gateways connecting Machines to MongoDB and AI Core.
- **Future State**: 3+ Gateways for high availability and load balancing.
- **Queue Management**: **Redis** will be deployed on ALL gateways to handle message queues, replacing direct synchronous connections for better resilience.

---

## 📚 Essential Documentation

### 📌 Pinned Directives
- **[OEM Data Collection SOP](docs/directives/oem_collection.md)**: Standard procedure for Oracle Enterprise Manager integration.
- **[Sentinel Prediction SOP](docs/directives/sentinel_prediction.md)**: Autonomous predictive maintenance protocol.
- **[Project Tasks & Roadmap](docs/TASKS.md)**: Current development status and backlog.

### 📖 Reference
- **[System Architecture](docs/ARCHITECTURE.md)**: Master architecture document.
- **[Qdrant Basics](docs/references/qdrant_basics.md)**: Understanding the Vector DB.
- **[Sentinel Walkthrough](docs/SENTINEL_WALKTHROUGH.md)**: Guide to the Intelligent DBA Sentinel System.

---

## 🛠️ Detailed Implementation Roadmap

To achieve the **Future Architecture** (3 Gateways, Redis, 4 Sources), the work is broken down into manageable phases.

### Phase 1: Infrastructure Foundations (Redis & Queueing)
- [x] **Redis Deployment**: Add Redis service to `docker-compose` and `ops/scripts`.
- [x] **Queue Implementation**: Create `RedisClient` in `api_agents/shared` for async messaging.
- [x] **Agent Decoupling**: Refactor Agents (Collector, Scout) to push data to Redis instead of direct MongoDB writes.
- [x] **Ingestion Workers**: Create dedicated workers to consume from Redis and write to MongoDB (Async Write).

### Phase 2: Distributed Gateway Architecture
- [x] **Gateway Config**: Define configuration profiles for `Gateway_01`, `Gateway_02`, `Gateway_03` (Infrastructure Ready).
- [ ] **Load Balancing**: Implement logic to distribute Agents across gateways.
- [ ] **Failover Logic**: If Gateway 01 fails, agents should fallback to Gateway 02.
- [ ] **Service Discovery**: Update `Scout` to register machines against specific Gateways.

### Phase 3: Data Source Unification (The 4 Streams)
- [ ] **Stream 1: CheckMK**: Finalize `checkmk_legacy_adapter` for stable event streaming.
- [ ] **Stream 2: OEM**: Optimize `oem_collector` for high-frequency polling.
- [ ] **Stream 3: Database**: Standardize `PredictorAgent` queries for direct DB health.
- [ ] **Stream 4: Machine**: Integrate `psutil` or `Telegraf` into `Watcher` agent for OS metrics (CPU/RAM/IO).

### Phase 4: Frontend & Visualization
- [ ] **Gateway Dashboard**: New UI view to monitor the status of the 3 Gateways + Redis Queues.
- [ ] **Unified Timeline**: Merge events from CheckMK, OEM, and Sentinel into a single timeline.
- [ ] **Real-time Updates**: Connect Frontend to Redis Pub/Sub for live status changes.

### Phase 5: Hardening & Production
- [ ] **Security**: Implement API Keys for Gateway-to-Gateway communication.
- [ ] **Disaster Recovery**: Simulate Gateway failure and verify Agent migration.
- [ ] **Performance Tuning**: Optimize Redis retention and MongoDB write throughput.

---

> _"From Chaos to Order" - Built for M-DN by the Advanced Agentic Coding Team_
