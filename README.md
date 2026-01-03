# 🤖 Nexi DBA AI Assistant

Sistema AI per la gestione di oltre 2000 database enterprise (Oracle, Postgres, MySQL, Cassandra).

## 🎯 Obiettivi del Progetto

| Fase | Obiettivo | Stato |
|------|-----------|-------|
| 1 | **Alerting Proattivo**: Prevedere problemi prima che accadano | 🔄 In Corso |
| 2 | **Supporto e Automazione**: Suggerimenti runbook, automazione task | 📋 Pianificato |
| 3 | **Operazioni Autonome**: Self-healing, capacity planning | 📋 Futuro |

## 🏗️ Architettura

```
┌─────────────────────────────────────────────────────────────────┐
│ AGENTS (5)                                                       │
│ Scout → Collector → Monitor → DailyAudit → CriticalAlert        │
├─────────────────────────────────────────────────────────────────┤
│ GATEWAY                                                          │
│ Redis Queues (cmd_in / result_out)                              │
├─────────────────────────────────────────────────────────────────┤
│ ORCHESTRATOR                                                     │
│ ├── Moduli AI: Architecture | Watcher | Tuning                  │
│ ├── Moduli Business: Performance | Capacity | Best Practices    │
│ └── RAG + LLM (Ollama) + Qdrant                                 │
├─────────────────────────────────────────────────────────────────┤
│ MONGODB CMDB (9 Collezioni)                                      │
│ inventory_databases | business_services | gateways |            │
│ discovery_queue | agent_runs | rag_knowledge_base |             │
│ monitoring_alerts | baselines | compliance_reports              │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Struttura del Progetto

| Directory | Descrizione |
|-----------|-------------|
| `Agents/` | 5 agenti SADA (Scout, Collector, Monitor, DailyAudit, CriticalAlert) |
| `Gateway/` | Routing Redis |
| `Orchestrator/` | Moduli AI + Business |
| `MongoDB/` | Schemi CMDB (9 collezioni) |
| `Clients/` | Dashboard React |
| `docker-lab/` | Ambiente di test Docker |

## 🚀 Avvio Rapido

### 1. Avviare l'ambiente di test
```bash
cd docker-lab
docker-compose up -d
```

### 2. Installare dipendenze Python
```bash
cd MongoDB
pip install -r requirements.txt
```

### 3. Inizializzare il database
```bash
cd MongoDB/scripts
python create_indexes.py
python seed_sample_data.py
```

### 4. Eseguire il Collector (test)
```bash
cd Agents/Collector
python main.py --targets pg-milano-prod.nexi.lab --gateway gw-milano
```

## 📋 Requisiti del Manager

| Requisito | Componente |
|-----------|------------|
| CENSIMENTO | `inventory_databases` + `business_services` |
| PERFORMANCE | `Orchestrator/modules/performance` |
| CAPACITY | `Orchestrator/modules/capacity` + `baselines` |
| BEST PRACTICES | `Orchestrator/modules/best_practices` |
| Audit Giornaliero | `Agents/DailyAudit` → `compliance_reports` |
| Alert Critici | `Agents/CriticalAlert` + Checkmk |

## 🔗 Integrazioni

| Sistema | Scopo |
|---------|-------|
| Checkmk | Dati di monitoring |
| Redis | Message queuing |
| MongoDB | Storage CMDB |
| Qdrant | Ricerca vettoriale |
| Ollama | LLM locale |
