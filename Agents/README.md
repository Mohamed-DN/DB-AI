# Agents

> Background workers for database discovery, monitoring, and alerting.

## Structure

```
Agents/
├── Scout/           # Auto-discovery
├── Collector/       # Metrics collection
├── Watcher/         # Log monitoring
├── CriticalAlert/   # Availability checks
├── CheckMK_Bridge/  # External sync
├── AIAssistant/     # Chat tools
├── DailyAudit/      # Scheduled reports
└── Monitor/         # Legacy
```

## Running Agents

```bash
# One-shot mode (recommended for testing)
python Agents/Scout/main.py --once

# Continuous mode (uses interval from config)
python Agents/Scout/main.py
```

## See Also
- [AGENTS.md](../AGENTS.md) - Full documentation
- [directives/](../directives/) - SOPs for each agent
