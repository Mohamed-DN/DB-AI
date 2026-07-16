# AI Assistant Context (Claude)

> This file provides context for AI assistants working on this repository.

## Project Identity
- **Name**: M-DN DBA AI (CMDB)
- **Purpose**: AI-powered database monitoring and management platform
- **Version**: V3 (Shadow Mode on V2 ports)

## Quick Context
```
What: Database inventory, monitoring, alerting, AI chat
Stack: Python/FastAPI + React + MongoDB + Ollama LLM
Ports: Backend 8000, Frontend 4002, MongoDB 28017
```

## Key Commands
| Action | Command |
|--------|---------|
| Start everything | `.\scripts\setup_v2.ps1` |
| Stop everything | `.\scripts\cleanup_v2.ps1` |
| Run discovery | `python Agents/Scout/main.py --once` |

## Architecture Overview
```
User → Frontend (React) → Backend (FastAPI) → MongoDB
                              ↓
                         Agents → Docker containers
                              ↓
                         Ollama LLM + Qdrant
```

## Critical Constraints
1. **V2 Ports**: Always use `28017` for MongoDB, `8000` for backend
2. **Environment**: Load from `.env.v2`, NOT `.env`
3. **Gateway Suffix**: Set `GATEWAY_SUFFIX=2` for V2 container discovery

## Directory Map
| Path | Purpose |
|------|---------|
| `Agents/` | Background workers (Scout, Collector, etc.) |
| `WebInterface/backend/` | FastAPI API |
| `WebInterface/frontend-react/` | React dashboard |
| `Orchestrator/` | LLM + RAG pipeline |
| `execution/` | Deterministic Python scripts |
| `directives/` | SOPs for AI orchestration |

## When Making Changes
1. Test with `.\scripts\setup_v2.ps1`
2. Commit to `v3` branch first
3. Sync to `v2` with `git checkout v2; git merge v3`
4. Push both branches
