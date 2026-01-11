# Nexi DBA AI (V3)

AI-powered CMDB and database monitoring platform. Discovers databases, collects metrics, raises alerts, and provides an AI-assisted dashboard.

## Quick Start

```powershell
# Clone and configure
git clone https://github.com/ThomasNexi/Nexi_DB_AI.git
cd Nexi_DB_AI
cp .env.example .env.v2

# Start everything (Zero-Config)
.\scripts\setup_v2.ps1
```

Dashboard: http://localhost:4002 | API Docs: http://localhost:9000/docs

## Architecture

This project follows a **3-Layer Architecture**. See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

| Layer | Location | Purpose |
|-------|----------|---------|
| Directives | `directives/*.md` | SOPs defining what to do |
| Orchestration | `WebInterface/backend/` | Decision making & routing |
| Execution | `execution/*.py` | Deterministic Python scripts |

## Agents

| Agent | Purpose | Command |
|-------|---------|---------|
| Scout | Auto-discovery | `python Agents/Scout/main.py --once` |
| Collector | Metrics | `python Agents/Collector/main.py --once` |
| CriticalAlert | Alerting | `python Agents/CriticalAlert/main.py --once` |

Or use the **Agents Panel** in the web UI.

## Configuration

Copy `.env.example` to `.env.v2` and configure:

- `MONGODB_*`: Database connection
- `OLLAMA_*`: LLM settings
- `ALERT_EMAIL`: DBA team email

See [.env.example](.env.example) for all options.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - 3-Layer Architecture
- [AGENTS.md](AGENTS.md) - Agent overview
- [MANIFEST.md](MANIFEST.md) - Port mappings
- [ROADMAP_V3.md](ROADMAP_V3.md) - Development roadmap
- [FOR_AI/PROJECT_CONTEXT.md](FOR_AI/PROJECT_CONTEXT.md) - AI assistant context

## License

Internal use only - Nexi Group.
