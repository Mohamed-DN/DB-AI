# MANIFEST

> Port mappings and service registry for Nexi DBA AI.

## V2 Ports (Shadow Mode)

### Infrastructure
| Service | Port | Container |
|---------|------|-----------|
| MongoDB | 28017 | nexi-mongodb2 |
| Mongo Express | 9081 | nexi-mongo-express2 |
| Redis | 7379 | nexi-redis2 |
| Ollama LLM | 12434 | nexi-ollama2 |
| Qdrant | 7333 | nexi-qdrant2 |
| Open WebUI | 4001 | nexi-open-webui2 |
| **Langfuse** | **3001** | nexi-langfuse2 |

### Application
| Service | Port |
|---------|------|
| Backend API | 9000 |
| Frontend UI | 4002 |

### Gateways
| Gateway | Port | Container |
|---------|------|-----------|
| Milano | 3221 | nexi-gw-milano2 |
| Bratislava | 3222 | nexi-gw-bratislava2 |
| Cairo | 3223 | nexi-gw-cairo2 |

### Sample Databases
| Database | Type | Port |
|----------|------|------|
| Milano PROD | PostgreSQL | 6432 |
| Milano DEV | PostgreSQL | 6433 |
| Milano STG | PostgreSQL | 6435 |
| Bratislava PROD | PostgreSQL | 6444 |
| Bratislava DEV | PostgreSQL | 6434 |
| Cairo Primary | Oracle | 2521 |
| Cairo Replica | Oracle | 2522 |

## Quick Reference

```powershell
# Start all
.\scripts\setup_v2.ps1

# Stop all
.\scripts\cleanup_v2.ps1
```

## URLs

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:4002 |
| API Docs | http://localhost:9000/docs |
| MongoDB UI | http://localhost:9081 |
| Ollama | http://localhost:12434 |
