# AI Project Context

> Master reference for AI assistants. Read this first.

## 🎯 What Is This Project?

**Nexi DBA AI** is an AI-powered CMDB (Configuration Management Database) for database infrastructure. It:

1. **Discovers** databases running in Docker
2. **Monitors** health, metrics, logs
3. **Alerts** when things go wrong
4. **Provides AI chat** for natural language queries

## 🏗️ Architecture (3-Layer)

```
┌─────────────────────────────────────────────────┐
│  LAYER 1: DIRECTIVES (directives/*.md)          │
│  What to do - SOPs in plain English             │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│  LAYER 2: ORCHESTRATION (You, the AI)           │
│  Decision making - Route to correct scripts     │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│  LAYER 3: EXECUTION (execution/*.py)            │
│  Do the work - Deterministic Python scripts     │
└─────────────────────────────────────────────────┘
```

## 🚀 Key Commands

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

## 📁 Directory Map

| Path | Layer | Purpose |
|------|-------|---------|
| `directives/` | L1 | SOPs (what to do) |
| `execution/` | L3 | Python scripts (how to do it) |
| `Agents/` | L3 | Background workers |
| `WebInterface/backend/` | L2 | FastAPI API |
| `WebInterface/frontend-react/` | - | React UI |
| `Orchestrator/` | L2/L3 | LLM + RAG |

## ⚠️ Critical Constraints

1. **Always V2 Ports**: Backend `9000`, MongoDB `28017`, Frontend `4002`
2. **Environment File**: Use `.env.v2` (not `.env`)
3. **Gateway Suffix**: `GATEWAY_SUFFIX=2` for V2 containers
4. **Branch Strategy**: Develop on `v3`, sync to `v2`

## 🔧 When You Need To...

| Task | Action |
|------|--------|
| Fix a bug | Edit code, test with `setup_v2.ps1`, commit to v3 |
| Add a feature | Update directive first, then implement |
| Debug "error loading" | Check backend logs, verify ports |
| Reset everything | Run `cleanup_v2.ps1` then `setup_v2.ps1` |

## 📊 MongoDB Collections

| Collection | Purpose |
|------------|---------|
| `inventory_databases` | Discovered databases |
| `monitoring_alerts` | Active alerts |
| `system_config` | Agent intervals, global settings |
| `business_services` | Service-to-DB mapping |
| `gateways` | SSH gateway info |

## 🔗 Related Files

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Technical architecture
- [AGENTS.md](../AGENTS.md) - Agent documentation
- [ROADMAP_V3.md](../ROADMAP_V3.md) - Development roadmap
- [README.md](../README.md) - Quick start
