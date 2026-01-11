# Agents Overview

> Background workers that discover, monitor, and alert on database infrastructure.

## Quick Reference

| Agent | Purpose | Interval Key | Command |
|-------|---------|--------------|---------|
| **Scout** | Auto-discovery | `scout_interval` | `python Agents/Scout/main.py --once` |
| **Collector** | Metrics collection | `collector_interval` | `python Agents/Collector/main.py --once` |
| **Watcher** | Log monitoring | `watcher_interval` | `python Agents/Watcher/main.py --once` |
| **CriticalAlert** | Availability checks | `criticalalert_interval` | `python Agents/CriticalAlert/main.py --once` |
| **CheckMK Bridge** | External sync | `checkmk_bridge_interval` | `python Agents/CheckMK_Bridge/main.py --once` |
| **AIAssistant** | Chat tools | - | (via API) |

## How Agents Work

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Docker     │────▶│   Agent     │────▶│  MongoDB    │
│  Containers │     │  (Python)   │     │  CMDB       │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │   Alerts    │
                    │   Emails    │
                    └─────────────┘
```

## Configuration

Intervals are stored in MongoDB `system_config` collection:

```javascript
db.system_config.find({})
// { key: "scout_interval", value: 60 }
// { key: "collector_interval", value: 120 }
```

Modify via API:
```bash
curl -X POST http://localhost:9000/api/config \
  -H "Content-Type: application/json" \
  -d '{"scout_interval": 30}'
```

Or use the **Agents Panel** in the web UI.

## Global Pause

All agents respect the `global_status` key:
- `RUNNING`: Agents execute normally
- `PAUSED`: Agents sleep (don't exit, just wait)

```bash
# Pause all agents
curl -X POST http://localhost:9000/api/system/status \
  -d '{"status": true}'
```

## Adding a New Agent

1. Create folder: `Agents/NewAgent/`
2. Add `main.py` with `--once` flag support
3. Add entry to `AGENTS_STATE` in `WebInterface/backend/main.py`
4. Add directive to `directives/new_agent.md`
5. Add interval key to `system_config`
