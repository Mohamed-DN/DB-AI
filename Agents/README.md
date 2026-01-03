# SADA: Semantic Auto-Discovery Architecture

AI agents for enterprise database management.

## Agents

| Agent | Schedule | Purpose |
|-------|----------|---------|
| **Scout** | 5 min | Discover new databases |
| **Collector** | Daily | Deep extraction (config, storage) |
| **Monitor** | 1 min | Sync Checkmk alerts |
| **DailyAudit** | Daily 02:00 | Full compliance check |
| **CriticalAlert** | Real-time | Critical error detection |

## Structure

```
Agents/
├── Scout/          # Discovery
├── Collector/      # Deep extraction
├── Monitor/        # Checkmk sync
├── DailyAudit/     # Daily compliance
├── CriticalAlert/  # Real-time alerts
└── main.py         # Orchestrator
```
