# RALPH ARCHITECTURAL REVIEW & OPTIMIZATION PLAN
**Role:** Senior DevOps Architect & AI System Optimizer
**Date:** 2024-05-23
**Status:** APPROVED FOR EXECUTION

---

### COMPONENTE 1: Frontend (React/Vite)

**Stato Attuale vs. Ralph Fix:**
> **Attuale:** Container Node/Nginx standard. Nessun healthcheck. Dipendenza "soft" dal backend.
> **Ralph Fix:** Aggiunto Healthcheck esplicito (curl localhost). Ottimizzazione dipendenza dal Backend con `service_healthy`. Configurazione Nginx già presente per SPA (OK).

**Specifica Tecnica Migliorata:**
> **Image:** `nginx:alpine` (Multi-stage build from Node 20)
> **Port:** 4002 (Host) -> 80 (Container)
> **Healthcheck:** `curl -f http://localhost:80/health || exit 1` (Interval: 30s)
> **Restart:** `unless-stopped`
> **Networks:** `nexi-lab2`

**Handshake (I/O):**
> **Riceve da:** Utente (Browser), WebSocket (Backend)
> **Invia a:** Backend API (Port 8000)

**LISTA MICRO-TASK:**
- [x] [FE-001] Aggiungere `healthcheck` in docker-compose per Frontend.
- [x] [FE-002] Aggiornare `depends_on` per attendere Backend `healthy`.

---

### COMPONENTE 2: Backend (FastAPI Gateway)

**Stato Attuale vs. Ralph Fix:**
> **Attuale:** Python 3.11 Slim. Manca endpoint `/health` dedicato per Docker. Manca healthcheck in compose.
> **Ralph Fix:** Creazione endpoint `/api/system/health` (o `/health`). Aggiunta Healthcheck in compose. Configurazione worker Uvicorn ottimizzata (rimosso reload in prod, ma mantenuto per lab).

**Specifica Tecnica Migliorata:**
> **Image:** Custom `api_agents/Dockerfile`
> **Port:** 8000
> **Env:** `MONGODB_URL`, `REDIS_URL`, `VICTORIAMETRICS_URL`
> **Healthcheck:** `curl -f http://localhost:8000/health || exit 1`
> **Volumes:** Bind mount code for dev (`./:/app` implied in lab).

**Handshake (I/O):**
> **Riceve da:** Frontend (HTTP/WS), Redis (Sub), Agents (Internal)
> **Invia a:** MongoDB, Redis (Pub), VictoriaMetrics, Qdrant, Ollama

**LISTA MICRO-TASK:**
- [x] [BE-001] Implementare endpoint `/health` in `system_router`.
- [x] [BE-002] Aggiungere `healthcheck` in docker-compose.
- [x] [BE-003] Configurare dipendenza stretta da Redis e Mongo (`service_healthy`).

---

### COMPONENTE 3: MongoDB (Primary Data Store)

**Stato Attuale vs. Ralph Fix:**
> **Attuale:** Mongo 7. Volume persistente presente. Auth configurata. Manca Healthcheck.
> **Ralph Fix:** Aggiunta Healthcheck nativo (`db.runCommand("ping")`).

**Specifica Tecnica Migliorata:**
> **Image:** `mongo:7`
> **Port:** 28017 (Host) -> 27017
> **Volume:** `mongodb_data_v2:/data/db`
> **Healthcheck:** `echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet`

**Handshake (I/O):**
> **Riceve da:** Backend, Workers (Scout, Collector)
> **Invia a:** Backend (Query Results)

**LISTA MICRO-TASK:**
- [x] [DB-001] Aggiungere `healthcheck` in docker-compose per MongoDB.

---

### COMPONENTE 4: Redis (Core & Gateways)

**Stato Attuale vs. Ralph Fix:**
> **Attuale:** Redis 7 Alpine. Auth attivata. **CRITICO:** Mancano i volumi di persistenza per TUTTE le istanze (Core + 3 Gateway). Rischio perdita code al riavvio. Manca Healthcheck.
> **Ralph Fix:** Aggiunta volumi nominativi (`redis_core_data`, `redis_milano_data`, etc.). Aggiunta Healthcheck `redis-cli ping`.

**Specifica Tecnica Migliorata:**
> **Image:** `redis:7-alpine`
> **Command:** `redis-server --appendonly yes --requirepass ...`
> **Volumes:**
>   - `redis_core_data:/data`
>   - `redis_milano_data:/data`
>   - (etc...)
> **Healthcheck:** `redis-cli -a nexi2024 ping | grep PONG`

**Handshake (I/O):**
> **Riceve da:** Backend (Task Queue), Agents (Metrics Push)
> **Invia a:** Celery Workers, Backend (Sub)

**LISTA MICRO-TASK:**
- [x] [RD-001] Creare volumi Docker per Redis Core e 3 Gateway.
- [x] [RD-002] Aggiungere `healthcheck` a tutte le istanze Redis.

---

### COMPONENTE 5: VictoriaMetrics (Time Series)

**Stato Attuale vs. Ralph Fix:**
> **Attuale:** Configurazione solida con retention 1 anno. Volume presente. Manca Healthcheck.
> **Ralph Fix:** Aggiunta Healthcheck su porta 8428.

**Specifica Tecnica Migliorata:**
> **Image:** `victoriametrics/victoria-metrics:latest`
> **Port:** 8428 (HTTP), 2003 (Graphite)
> **Volume:** `victoriametrics_data:/victoria-metrics-data`
> **Healthcheck:** `wget -qO- http://localhost:8428/health`

**Handshake (I/O):**
> **Riceve da:** OEM Collector, Sentinel Agent, Graphite (CheckMK)
> **Invia a:** Grafana, Sentinel Predictor

**LISTA MICRO-TASK:**
- [x] [VM-001] Aggiungere `healthcheck` in docker-compose.

---

### COMPONENTE 6: Qdrant (Vector DB)

**Stato Attuale vs. Ralph Fix:**
> **Attuale:** Volume presente. Configurazione OK. Manca Healthcheck.
> **Ralph Fix:** Aggiunta Healthcheck `/readyz`.

**Specifica Tecnica Migliorata:**
> **Image:** `qdrant/qdrant:latest`
> **Port:** 7333 (Host) -> 6333
> **Volume:** `qdrant_data_v2:/qdrant/storage`
> **Healthcheck:** `curl -f http://localhost:6333/readyz || exit 1`

**Handshake (I/O):**
> **Riceve da:** RAG Pipeline (Embeddings)
> **Invia a:** RAG Pipeline (Context Retrieval)

**LISTA MICRO-TASK:**
- [x] [QD-001] Aggiungere `healthcheck` in docker-compose.

---

### COMPONENTE 7: Ollama (LLM Inference)

**Stato Attuale vs. Ralph Fix:**
> **Attuale:** Volume presente. Manca Healthcheck.
> **Ralph Fix:** Aggiunta Healthcheck.

**Specifica Tecnica Migliorata:**
> **Image:** `ollama/ollama:latest`
> **Port:** 12434 -> 11434
> **Volume:** `ollama_data_v2:/root/.ollama`
> **Healthcheck:** `curl -f http://localhost:11434/ || exit 1`

**Handshake (I/O):**
> **Riceve da:** Backend (Prompt)
> **Invia a:** Backend (Completion)

**LISTA MICRO-TASK:**
- [x] [LLM-001] Aggiungere `healthcheck` in docker-compose.

---
**Generato da:** Jules (Ralph Mode)
