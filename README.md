# Nexi DBA AI (CMDB V3)

> **Status**: Active Development (Shadow Mode on V2)
> **Goal**: AI-powered Autonomous Database Administration & CMDB

## 🗺️ Start Here: The "Big Picture"

This repository builds an AI Agent that autonomously monitors, documents, and eventually manages enterprise databases (Oracle & PostgreSQL).

### 1. The Pipeline ("From Chaos to Order")
How do we turn raw SQL output into intelligent dashboards?
👉 **[Read: PIPELINE_EXPLAINED.md](docs/pipeline_explained.md)** (Essential context)

### 2. The Data Model ("The Contract")
What exactly are we collecting? (WAL, RMAN, ASM, Replication Stats)
👉 **[Read: Data Ingestion Specs](docs/data_ingestion_specs.md)**

### 3. The "How-To" for Agents
What commands do the agents run to get this data?
👉 **[Read: Agent Extraction Commands](docs/agent_extraction_commands.md)**

---

## 📂 Repository Structure

Below is a comprehensive guide to the repository's layout.

| Directory | Role | Description |
|-----------|------|-------------|
| **`Agents/`** | **The Hands** | Contains the `Scout` (discovery), `Collector` (monitoring), and other agents that interact with databases. |
| **`Orchestrator/`** | **The Brain** | Houses the LLM logic, RAG pipeline, and vector database interactions. |
| **`WebInterface/`** | **The Face** | The User Interface. `backend/` (FastAPI) and `frontend-react/` (React Dashboard). |
| **`MongoDB/`** | **The Memory** | Initialization scripts, schemas, and structure for the MongoDB metadata store. |
| **`docker-lab/`** | **The World** | Simulation environment with Oracle, PostgreSQL, and other containers for testing. |
| **`scripts/`** | **Tools** | Powershell and Shell scripts for system startup (`setup_v2.ps1`), cleanup, and maintenance. |
| **`execution/`** | **Actions** | Deterministic Python scripts typically called by Agents or the Orchestrator for specific tasks. |
| **`directives/`** | **SOPs** | Standard Operating Procedures and text protocols used to guide the AI Agents. |
| **`Gateway/`** | **Network** | Configuration for the API Gateway and Redis services. |
| **`Tests/`** | **Verification** | Integration and unit tests for the system. |
| **`docs/`** | **Docs** | Detailed documentation like pipeline explanations and data specs. |

---

## 🚀 Quick Start (Mac/Linux)

1.  **Setup Environment**:
    ```bash
    ./scripts/setup_v2.sh
    ```
2.  **Access Dashboard**:
    Open `http://localhost:4002`
3.  **Run Discovery (Manual Trigger)**:
    ```bash
    python Agents/Scout/main.py --once
    ```

---

## 🛠️ Developer Notes / Roadmap

*   **Phase 1 (Done)**: Foundations, Docker Lab, Schemas.
*   **Phase 2 (Active)**: Agent Autonomy. Agents now autonomously extract deep metadata (RMAN, WAL) without human help.
*   **Phase 3**: AI ETL & Self-Healing.
