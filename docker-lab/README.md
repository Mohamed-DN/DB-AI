# Docker Lab

> Local infrastructure for development and testing.

## Quick Start

```powershell
# Start V2 infra
cd docker-lab
docker-compose -f docker-compose-v2.yml up -d

# Or use the setup script (recommended)
.\scripts\setup_v2.ps1
```

## Services (V2)

| Service | Port | Purpose |
|---------|------|---------|
| MongoDB | 28017 | CMDB database |
| Mongo Express | 9081 | Web UI for MongoDB |
| Redis | 7379 | Cache |
| Ollama | 12434 | LLM |
| Qdrant | 7333 | Vector DB |
| Open WebUI | 4001 | Chat UI (optional) |

## Sample Databases

| Container | Type | Port |
|-----------|------|------|
| nexi-pg-milano-prod2 | PostgreSQL | 6432 |
| nexi-pg-milano-dev2 | PostgreSQL | 6433 |
| nexi-oracle-cairo-primary2 | Oracle | 2521 |

## Cleanup

```powershell
# Remove all V2 containers and volumes
.\scripts\cleanup_v2.ps1

# Or manually
docker-compose -f docker-compose-v2.yml down -v
```
