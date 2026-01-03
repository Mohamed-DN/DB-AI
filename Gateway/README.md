# 🔀 Gateway Layer

Il Gateway funge da hub centrale di routing tra gli agenti remoti e l'orchestrator.

## 📋 Componenti

### Python Gateway
- Inoltra comandi dall'Orchestrator agli Agenti
- Raccoglie risultati dagli Agenti verso l'Orchestrator

### Redis Queues

| Queue | Direzione | Scopo |
|-------|-----------|-------|
| `cmd_in` | Orchestrator → Agent | Comandi da eseguire |
| `result_out` | Agent → Orchestrator | Risultati esecuzione |

## 🔄 Flusso Dati

```
Orchestrator → Redis (cmd_in) → Gateway → Agent (via SSH)
Agent → Gateway → Redis (result_out) → Orchestrator
```

## ⚙️ Configurazione

Vedere `redis_config/` per le impostazioni di connessione Redis.

## 🚀 Avvio

```bash
# Redis è incluso nell'ambiente Docker lab
cd ../docker-lab
docker-compose up -d redis
```
