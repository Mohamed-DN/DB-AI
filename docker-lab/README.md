# 🐳 Docker Lab

> Local infrastructure for development and testing.

---

## 🎯 AI Context

```yaml
Purpose: Containerized infrastructure for V2 shadow mode
Compose File: docker-compose-v2.yml
Network: docker-lab_nexi-lab2 (172.21.0.0/16)
Start: .\scripts\setup_v2.ps1
Stop: .\scripts\cleanup_v2.ps1
```

---

## 🏗️ Infrastructure Overview

```mermaid
flowchart TB
    subgraph DockerLab["🐳 Docker Lab Network (172.21.0.0/16)"]
        subgraph Core["🏢 Core Services"]
            MongoDB[(MongoDB<br/>:28017)]
            MongoExpress[Mongo Express<br/>:9081]
            Redis[(Redis<br/>:7379)]
        end

        subgraph AI["🤖 AI Services"]
            Ollama[Ollama<br/>:12434]
            Qdrant[(Qdrant<br/>:7333)]
            OpenWebUI[Open WebUI<br/>:4001]
        end

        subgraph Observability["📊 Observability"]
            Langfuse[Langfuse<br/>:3001]
            LangfuseDB[(Langfuse PG)]
        end

        subgraph Gateways["🔗 Gateways"]
            GW1[gw-milano2<br/>:3221]
            GW2[gw-bratislava2<br/>:3222]
            GW3[gw-cairo2<br/>:3223]
        end

        subgraph Databases["🗄️ Sample Databases"]
            PG1[(pg-milano-prod<br/>:6432)]
            PG2[(pg-milano-dev<br/>:6433)]
            Oracle1[(oracle-cairo<br/>:2521)]
        end
    end

    MongoDB --- MongoExpress
    Langfuse --- LangfuseDB
    GW1 --> PG1 & PG2
    GW3 --> Oracle1
```

---

## 📋 Service Reference

### Core Services

| Service | Container | Port | IP |
|---------|-----------|------|-----|
| MongoDB | nexi-mongodb2 | 28017 | 172.21.0.10 |
| Mongo Express | nexi-mongo-express2 | 9081 | - |
| Redis | nexi-redis2 | 7379 | - |

### AI Services

| Service | Container | Port | IP |
|---------|-----------|------|-----|
| Ollama | nexi-ollama2 | 12434 | 172.21.0.11 |
| Qdrant | nexi-qdrant2 | 7333 | 172.21.0.12 |
| Open WebUI | nexi-open-webui2 | 4001 | - |

### Observability

| Service | Container | Port | IP |
|---------|-----------|------|-----|
| Langfuse | nexi-langfuse2 | 3001 | 172.21.0.21 |
| Langfuse DB | nexi-langfuse-db2 | - | 172.21.0.20 |

### Gateways

| Gateway | Container | Port | Location |
|---------|-----------|------|----------|
| Milano | nexi-gw-milano2 | 3221 | Italy |
| Bratislava | nexi-gw-bratislava2 | 3222 | Slovakia |
| Cairo | nexi-gw-cairo2 | 3223 | Egypt |

---

## 🛠️ Commands

```powershell
# Start all V2 infrastructure
cd docker-lab
docker-compose -f docker-compose-v2.yml up -d

# Or use setup script (recommended)
.\scripts\setup_v2.ps1

# Stop and remove everything
.\scripts\cleanup_v2.ps1

# View running containers
docker ps --filter "name=nexi" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

---

## 📁 Files

```
docker-lab/
├── docker-compose-v2.yml    # V2 shadow mode
├── docker-compose.yml       # V1 (legacy)
└── init/                    # Init scripts
```

---

## 🔗 Related

- [MANIFEST.md](../MANIFEST.md) - Full port reference
- [scripts/setup_v2.ps1](../scripts/setup_v2.ps1) - Startup script
