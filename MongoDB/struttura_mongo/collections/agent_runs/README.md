# Agent Runs Collection

Log delle esecuzioni degli agenti SADA (Scout e Collector).

## Scopo

- **Auditing**: Tracciare ogni esecuzione.
- **Debugging**: Analizzare errori.
- **Metriche**: Dashboard sulle performance degli agenti.

## Indici

```javascript
db.agent_runs.createIndex({ "agent_type": 1, "started_at": -1 }, { name: "idx_agent_history" });
db.agent_runs.createIndex({ "status": 1 }, { name: "idx_run_status" });
```
