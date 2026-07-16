# 📋 MANIFEST

> Port mappings and service registry for M-DN DBA AI.

---

## 🎯 AI Context

```yaml
Purpose: Central port reference for V2 shadow mode
Version: V2 (all services suffixed with "2")
Network: docker-lab_m-dn-lab2 (172.21.0.0/16)
```

---

## 🏢 Service Map

```mermaid
flowchart TB
    subgraph Application["🖥️ Application Layer"]
        FE[Frontend<br/>:4002]
        BE[Backend API<br/>:8000]
    end

    subgraph Core["🏢 Core Services"]
        MongoDB[(MongoDB<br/>:28017)]
        MongoUI[Mongo Express<br/>:9081]
        Redis[(Redis<br/>:7379)]
    end

    subgraph AI["🤖 AI Services"]
        Ollama[Ollama<br/>:12434]
        Qdrant[(Qdrant<br/>:7333)]
        WebUI[Open WebUI<br/>:4001]
    end

    subgraph Observability["📊 Observability"]
        Langfuse[Langfuse<br/>:3001]
    end

    subgraph Gateways["🔗 Gateways"]
        GW1[Milano :3221]
        GW2[Bratislava :3222]
        GW3[Cairo :3223]
    end

    subgraph Databases["🗄️ Sample DBs"]
        PG1[PG Milano Prod :6432]
        PG2[PG Milano Dev :6433]
        Oracle[Oracle Cairo :2521]
    end

    FE --> BE --> MongoDB
    BE --> Ollama
    GW1 --> PG1 & PG2
    GW3 --> Oracle
```

---

## 📋 Port Reference

### Application

| Service | Port | Container |
|---------|------|-----------|
| **Backend API** | 8000 | (process) |
| **Frontend UI** | 4002 | (process) |

### Infrastructure

| Service | Port | Container |
|---------|------|-----------|
| MongoDB | 28017 | m-dn-mongodb2 |
| Mongo Express | 9081 | m-dn-mongo-express2 |
| Redis | 7379 | m-dn-redis2 |
| Ollama LLM | 12434 | m-dn-ollama2 |
| Qdrant | 7333 | m-dn-qdrant2 |
| Open WebUI | 4001 | m-dn-open-webui2 |
| **Langfuse** | **3001** | m-dn-langfuse2 |

### Gateways

| Gateway | Port | Container |
|---------|------|-----------|
| Milano | 3221 | m-dn-gw-milano2 |
| Bratislava | 3222 | m-dn-gw-bratislava2 |
| Cairo | 3223 | m-dn-gw-cairo2 |

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

---

## 🔗 URLs

| Service | URL |
|---------|-----|
| 🖥️ Dashboard | http://localhost:4002 |
| 📡 API Docs | http://localhost:8000/docs |
| 🗄️ MongoDB UI | http://localhost:9081 |
| 📊 Langfuse | http://localhost:3001 |
| 🤖 Ollama | http://localhost:12434 |

---

## 🛠️ Commands

```powershell
# Start all
.\scripts\setup_v2.ps1

# Stop all
.\scripts\cleanup_v2.ps1

# Check running containers
docker ps --filter "name=m-dn" --format "table {{.Names}}\t{{.Ports}}"
```
