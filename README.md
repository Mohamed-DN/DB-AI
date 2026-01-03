# Nexi DBA AI Assistant

AI-powered DBA support for 2000+ enterprise databases.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ AGENTS (5)                                                       │
│ Scout → Collector → Monitor → DailyAudit → CriticalAlert        │
├─────────────────────────────────────────────────────────────────┤
│ GATEWAY                                                          │
│ Redis Queues (cmd_in / result_out)                              │
├─────────────────────────────────────────────────────────────────┤
│ ORCHESTRATOR                                                     │
│ ├── AI Modules: Architecture | Watcher | Tuning                 │
│ ├── Business Modules: Performance | Capacity | Best Practices   │
│ └── RAG + LLM (Ollama) + Qdrant                                 │
├─────────────────────────────────────────────────────────────────┤
│ MONGODB CMDB (9 Collections)                                     │
│ inventory_databases | business_services | gateways |            │
│ discovery_queue | agent_runs | rag_knowledge_base |             │
│ monitoring_alerts | baselines | compliance_reports              │
└─────────────────────────────────────────────────────────────────┘
```

## � Manager Requirements Mapping

| Requirement | Component |
|-------------|-----------|
| CENSIMENTO (Census) | `inventory_databases` + `business_services` |
| PERFORMANCE | `Orchestrator/modules/performance` |
| CAPACITY | `Orchestrator/modules/capacity` + `baselines` |
| BEST PRACTICES | `Orchestrator/modules/best_practices` |
| Daily Audit | `Agents/DailyAudit` → `compliance_reports` |
| Critical Alerts | `Agents/CriticalAlert` + Checkmk |

## � Project Structure

- **Agents/**: 5 agents (Scout, Collector, Monitor, DailyAudit, CriticalAlert)
- **Gateway/**: Redis routing
- **Orchestrator/**: AI + Business modules
- **MongoDB/**: CMDB schemas (9 collections)
- **Clients/**: Dashboard
