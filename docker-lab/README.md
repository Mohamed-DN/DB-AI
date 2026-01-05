# 🐳 Docker Lab - Ambiente di Test

Questa directory contiene la configurazione Docker per l'ambiente di sviluppo e test.

## 🚀 Avvio

```powershell
cd docker-lab
docker-compose up -d
```

## 📦 Servizi Inclusi

### Infrastruttura

| Servizio | Container | Porta | Descrizione |
|----------|-----------|-------|-------------|
| MongoDB | `nexi-mongodb` | 27017 | Database CMDB |
| Mongo Express | `nexi-mongo-express` | 8081 | UI MongoDB |
| Redis | `nexi-redis` | 6379 | Message queue |
| Qdrant | `nexi-qdrant` | 6333 | Vector DB per RAG |
| Ollama | `nexi-ollama` | 11434 | LLM locale |

### Database di Test

| Database | Container | Tipo | Gateway |
|----------|-----------|------|---------|
| NEXI-PG-MILANO-PROD | `nexi-pg-milano-prod` | PostgreSQL | gw-milano |
| NEXI-PG-MILANO-STG | `nexi-pg-milano-stg` | PostgreSQL | gw-milano |
| NEXI-PG-MILANO-DEV | `nexi-pg-milano-dev` | PostgreSQL | gw-milano |
| NEXI-PG-BRATISLAVA-PROD | `nexi-pg-bratislava-prod` | PostgreSQL | gw-bratislava |
| NEXI-PG-BRATISLAVA-DEV | `nexi-pg-bratislava-dev` | PostgreSQL | gw-bratislava |
| NEXI-ORACLE-CAIRO-PRIMARY | `nexi-oracle-cairo-primary` | Oracle XE | gw-cairo |
| NEXI-ORACLE-CAIRO-REPLICA | `nexi-oracle-cairo-replica` | Oracle XE | gw-cairo |

### Gateway

| Gateway | Container | Datacenter |
|---------|-----------|------------|
| gw-milano | `nexi-gw-milano` | Milano, Italy |
| gw-bratislava | `nexi-gw-bratislava` | Bratislava, Slovakia |
| gw-cairo | `nexi-gw-cairo` | Cairo, Egypt |

---

## 🏷️ Labels Docker

I container database devono avere queste labels per essere rilevati da Scout:

```yaml
labels:
  - "db.type=POSTGRES"           # o ORACLE, MYSQL, etc.
  - "db.name=nexi-pg-milano-prod"
  - "db.env=PROD"                # o DEV, STG
  - "db.gateway=gw-milano"
```

---

## 🔧 Comandi Utili

### Verifica status

```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Verifica logs

```powershell
docker logs nexi-mongodb
docker logs nexi-ollama
```

### Stop/Start gateway (per test alert)

```powershell
docker stop nexi-gw-cairo    # Trigger DB_DOWN
docker start nexi-gw-cairo   # Trigger DB_RECOVERY
```

### Accesso MongoDB

```powershell
docker exec -it nexi-mongodb mongosh nexi_cmdb
```

### Pull modelli Ollama

```powershell
docker exec nexi-ollama ollama pull llama3:8b
docker exec nexi-ollama ollama pull qwen2.5:14b
```

---

## 🔄 Reset Ambiente

```powershell
docker-compose down -v    # Stop e rimuovi volumi
docker-compose up -d      # Riavvia fresh
```

---

## 📝 Aggiungere un Nuovo Database

1. Aggiungi al `docker-compose.yaml`:
   ```yaml
   nexi-pg-newdb:
     image: postgres:15
     container_name: nexi-pg-newdb
     labels:
       - "db.type=POSTGRES"
       - "db.name=nexi-pg-newdb"
       - "db.env=PROD"
       - "db.gateway=gw-milano"
     environment:
       POSTGRES_USER: postgres
       POSTGRES_PASSWORD: postgres
     networks:
       - nexi-data-network
   ```

2. Riavvia:
   ```powershell
   docker-compose up -d
   ```

3. Scout lo rileverà automaticamente al prossimo ciclo.
