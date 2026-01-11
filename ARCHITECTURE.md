# Nexi DBA AI - Architecture

## 3-Layer Architecture

This project follows a **3-Layer Architecture** that separates concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 1: DIRECTIVES                      │
│                     (directives/*.md)                       │
│   SOPs defining WHAT to do, inputs, outputs, edge cases     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  LAYER 2: ORCHESTRATION                     │
│              (AI Assistant / Backend API)                   │
│   Decision making, routing, error handling, learning        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 3: EXECUTION                       │
│                    (execution/*.py)                         │
│   Deterministic scripts, API calls, DB operations           │
└─────────────────────────────────────────────────────────────┘
```

## Why This Works

LLMs are probabilistic - they can make mistakes. Business logic is deterministic - it must be consistent. This architecture:

1. **Directives** = Human-readable instructions (like giving tasks to an employee)
2. **Orchestration** = AI reads directives, decides which scripts to run
3. **Execution** = Reliable Python scripts that do the actual work

## Directory Structure

```
Nexi_DB_AI/
├── directives/           # Layer 1: SOPs (Markdown)
├── execution/            # Layer 3: Deterministic scripts
├── Agents/               # Background workers
├── Orchestrator/         # LLM + RAG pipeline
├── WebInterface/
│   ├── backend/          # FastAPI (Orchestration Layer)
│   └── frontend-react/   # React Dashboard
├── docker-lab/           # Infrastructure (MongoDB, Ollama, DBs)
├── scripts/              # PowerShell utilities
└── .env.v2               # Configuration
```

## Data Flow

```
User Request → Frontend → Backend API → Agent/Script → MongoDB
                                    ↓
                              Orchestrator
                                    ↓
                            Ollama LLM + Qdrant
```

## Agents

| Agent | Purpose | Directive |
|-------|---------|-----------|
| Scout | Auto-discovery | `database_discovery.md` |
| Collector | Metrics | `metric_collection.md` |
| Watcher | Log monitoring | `container_monitoring.md` |
| CriticalAlert | Alerting | `alert_processing.md` |
| CheckMK Bridge | External sync | `checkmk_sync.md` |
| AIAssistant | Chat tools | `ai_chat.md` |

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

Key variables:
- `MONGODB_*`: Database connection
- `OLLAMA_*`: LLM configuration
- `QDRANT_*`: Vector database
- `GATEWAY_SUFFIX`: V1 vs V2 mode

## Quick Reference

| Command | Purpose |
|---------|---------|
| `.\scripts\setup_v2.ps1` | Start everything |
| `.\scripts\cleanup_v2.ps1` | Stop and clean |
| `python execution/discover_docker_databases.py` | Manual discovery |
