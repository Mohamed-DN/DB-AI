# Agents

> Background workers for database discovery, monitoring, and alerting.

---

## 🎯 AI Context

```yaml
Location: Agents/
Purpose: Autonomous background workers
Trigger: python Agents/{name}/main.py --once
Output: MongoDB collections
```

---

## 📋 Agent Reference

| Agent | Purpose | Command |
|-------|---------|---------|
| Scout | Auto-discovery | `python Agents/Scout/main.py --once` |
| Collector | Metrics | `python Agents/Collector/main.py --once` |
| Watcher | Log monitoring | `python Agents/Watcher/main.py` |
| CriticalAlert | Alerting | `python Agents/CriticalAlert/main.py --once` |

---

## 🔗 Related

- [../AGENTS.md](../AGENTS.md) - Full documentation
