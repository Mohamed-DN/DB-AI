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

| Directory | Component | "Who is this?" |
|-----------|-----------|----------------|
| **`Agents/`** | **The Hands** | Python scripts (`Scout`) that visit databases and "fish" for data. Now capable of **Deep Extraction** (Docker Exec). |
| **`Orchestrator/`** | **The Brain** | LLM-powered logic that cleans raw data (Currently using direct extraction for V2). |
| **`WebInterface/`** | **The Face** | React Frontend + FastAPI Backend. Where you verify the data. |
| **`MongoDB/`** | **The Memory** | Stores the JSON inventory. |
| **`docker-lab/`** | **The World** | Simulation of the Datacenter (Oracle RAC, Postgres Enterprise). |

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
