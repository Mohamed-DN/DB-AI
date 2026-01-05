# 🤖 Nexi DBA AI - Intelligent Database Management System

> **AI-Powered CMDB with Real-Time Monitoring, Log Forensics, and Autonomous Analysis**

Sistema enterprise per la gestione intelligente di database Oracle, PostgreSQL, MySQL e Cassandra con capacità di auto-discovery, alerting predittivo e diagnosi AI-powered.

---

## 📋 Indice

1. [Panoramica](#-panoramica)
2. [Architettura](#-architettura)
3. [Prerequisiti](#-prerequisiti)
4. [Installazione Rapida](#-installazione-rapida)
5. [Struttura del Repository](#-struttura-del-repository)
6. [Componenti](#-componenti)
7. [Configurazione](#-configurazione)
8. [Dashboard Web](#-dashboard-web)
9. [Troubleshooting](#-troubleshooting)

---

## 🎯 Panoramica

### Cosa fa questo sistema?

| Funzionalità | Descrizione |
|--------------|-------------|
| **Auto-Discovery** | Rileva automaticamente database in Docker containers |
| **CMDB** | Inventario centralizzato in MongoDB con metriche deep |
| **Alerting** | Email real-time per DB down/recovery con anti-spam |
| **Log Forensics** | Streaming log con rilevamento errori ORA-*, TNS-* |
| **AI Analysis** | RAG pipeline con Ollama + Qdrant per diagnosi |
| **CheckMK Integration** | Importa metriche esterne (CPU, RAM, Disk) |
| **Dashboard** | UI moderna per monitoraggio e controllo agenti |

### Fasi del Progetto

| Fase | Obiettivo | Stato |
|------|-----------|-------|
| 1 | **Alerting Proattivo**: Prevedere problemi prima che accadano | ✅ Completato |
| 2 | **Deep Observability**: Tablespaces, RMAN, DataGuard | ✅ Completato |
| 3 | **AI Forensics**: RAG + LLM per root cause analysis | ✅ Completato |
| 4 | **Operazioni Autonome**: Self-healing, capacity planning | 📋 Futuro |

---

## 🏗️ Architettura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (localhost:3000)                        │
│                    Dashboard React/Vanilla JS                            │
├─────────────────────────────────────────────────────────────────────────┤
│                         BACKEND (localhost:8000)                         │
│                         FastAPI REST API                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                              AGENTS (6)                                  │
│  ┌─────────┐ ┌──────────────┐ ┌─────────┐ ┌────────────────┐           │
│  │  Scout  │ │CriticalAlert │ │ Watcher │ │ForensicAnalyzer│           │
│  │ (60s)   │ │   (30s)      │ │  (10s)  │ │     (30s)      │           │
│  └────┬────┘ └──────┬───────┘ └────┬────┘ └───────┬────────┘           │
│       │             │              │              │                     │
│  ┌────┴────┐ ┌──────┴───────┐                                          │
│  │CheckMK  │ │  Collector   │                                          │
│  │ Bridge  │ │   (30s)      │                                          │
│  │ (60s)   │ │              │                                          │
│  └─────────┘ └──────────────┘                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                           ORCHESTRATOR                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ LLM Client   │  │ Qdrant Client│  │ RAG Pipeline │                  │
│  │ (Ollama)     │  │ (Vector DB)  │  │              │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
├─────────────────────────────────────────────────────────────────────────┤
│                         DATA LAYER                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │   MongoDB    │  │    Qdrant    │  │    Redis     │  │   Ollama    │ │
│  │   (CMDB)     │  │  (Vectors)   │  │   (Queue)    │  │   (LLM)     │ │
│  │ :27017       │  │   :6333      │  │   :6379      │  │  :11434     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Prerequisiti

### Software Richiesto

| Software | Versione Minima | Scopo |
|----------|-----------------|-------|
| **Docker Desktop** | 4.0+ | Containers per servizi |
| **Python** | 3.10+ | Agenti e backend |
| **Node.js** | 18+ | Frontend (opzionale per dev) |
| **Git** | 2.30+ | Version control |

### Porte Richieste

| Porta | Servizio |
|-------|----------|
| 3000 | Frontend Dashboard |
| 8000 | Backend API |
| 27017 | MongoDB |
| 8081 | Mongo Express |
| 6333 | Qdrant |
| 6379 | Redis |
| 11434 | Ollama LLM |

### Hardware Consigliato

| Componente | Minimo | Consigliato |
|------------|--------|-------------|
| RAM | 16 GB | 32 GB |
| CPU | 4 cores | 8+ cores |
| GPU | - | NVIDIA con 8GB+ VRAM (per Ollama) |
| Disco | 50 GB | 100+ GB SSD |

---

## 🚀 Installazione Rapida

### Step 1: Clonare il Repository

```powershell
git clone https://github.com/ThomasNexi/Nexi_DB_AI.git
cd Nexi_DB_AI
```

### Step 2: Avviare i Servizi Docker

```powershell
cd docker-lab
docker-compose up -d
```

Questo avvia:
- MongoDB + Mongo Express
- Redis
- Qdrant (Vector DB)
- Ollama (LLM)
- Database di test (PostgreSQL, Oracle)

### Step 3: Installare Dipendenze Python

```powershell
pip install fastapi uvicorn pymongo requests python-dotenv pydantic
```

### Step 4: Scaricare Modelli LLM

```powershell
.\pull_models.ps1
```

Oppure manualmente:
```powershell
docker exec nexi-ollama ollama pull llama3:8b
docker exec nexi-ollama ollama pull qwen2.5:14b
```

### Step 5: Avviare il Sistema

```powershell
.\WebInterface\run_dashboard.ps1
```

Questo avvia:
- ✅ Backend FastAPI (porta 8000)
- ✅ Frontend Dashboard (porta 3000)
- ✅ Agenti Scout e CriticalAlert

### Step 6: Aprire la Dashboard

Vai a: **http://localhost:3000**

---

## 📁 Struttura del Repository

```
Nexi_DB_AI/
├── Agents/                      # 🤖 Agenti di monitoraggio
│   ├── Scout/                   # Auto-discovery database
│   │   └── main.py             
│   ├── CriticalAlert/           # Alerting via email
│   │   └── critical_alert.py   
│   ├── Watcher/                 # Log streaming e forensics
│   │   ├── main.py              # Streaming log container
│   │   └── ai_analyzer.py       # Analisi AI degli errori
│   ├── CheckMK_Bridge/          # Importa metriche esterne
│   │   └── main.py             
│   └── Collector/               # Metriche performance
│       └── main.py             
│
├── Orchestrator/                # 🧠 Core AI
│   ├── src/
│   │   └── mongo_proxy.py       # Interfaccia MongoDB
│   ├── llm/
│   │   └── ollama_client.py     # Client Ollama LLM
│   ├── vector_db/
│   │   └── qdrant_client.py     # Client Qdrant
│   ├── rag/
│   │   └── rag_pipeline.py      # RAG per diagnosi
│   └── config/
│       └── llm_config.py        # Configurazione modelli
│
├── WebInterface/                # 🌐 Dashboard
│   ├── frontend/
│   │   ├── index.html           # UI principale
│   │   ├── app.js               # Logica frontend
│   │   └── style.css            # Stili
│   ├── backend/
│   │   └── main.py              # API FastAPI
│   └── run_dashboard.ps1        # Script avvio
│
├── MongoDB/                     # 📊 Schema CMDB
│   ├── schemas/                 # Definizioni JSON Schema
│   └── scripts/                 # Script di utilità
│
├── docker-lab/                  # 🐳 Ambiente Docker
│   └── docker-compose.yaml      # Tutti i servizi
│
├── emails/                      # 📧 Archivio email inviate
│
└── docs/                        # 📚 Documentazione aggiuntiva
```

---

## 🔧 Componenti

### Agenti

| Agente | File | Scopo | Intervallo Default |
|--------|------|-------|-------------------|
| **Scout** | `Agents/Scout/main.py` | Auto-discovery database Docker | 60s |
| **CriticalAlert** | `Agents/CriticalAlert/critical_alert.py` | Invio email per alert | 30s |
| **Watcher** | `Agents/Watcher/main.py` | Streaming log containers | 10s |
| **ForensicAnalyzer** | `Agents/Watcher/ai_analyzer.py` | Analisi AI errori | 30s |
| **CheckMK_Bridge** | `Agents/CheckMK_Bridge/main.py` | Sync metriche esterne | 60s |
| **Collector** | `Agents/Collector/main.py` | Metriche performance | 30s |

### Orchestrator

| Modulo | File | Scopo |
|--------|------|-------|
| **MongoProxy** | `Orchestrator/src/mongo_proxy.py` | Interfaccia MongoDB via `mongosh` |
| **OllamaClient** | `Orchestrator/llm/ollama_client.py` | Chiamate a Ollama LLM |
| **QdrantClient** | `Orchestrator/vector_db/qdrant_client.py` | Ricerca semantica |
| **RAGPipeline** | `Orchestrator/rag/rag_pipeline.py` | Retrieval + Generation |

### Database Schema (MongoDB)

| Collezione | Scopo |
|------------|-------|
| `inventory_databases` | Inventario database con deep_observability |
| `monitoring_alerts` | Alert generati dagli agenti |
| `system_config` | Configurazione intervalli agenti |
| `gateways` | Mappa gateway per datacenter |
| `business_services` | Mapping DB ↔ servizi business |

---

## ⚙️ Configurazione

### Variabili d'Ambiente

Crea un file `.env` nella root:

```env
# MongoDB
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=nexi_cmdb

# Email SMTP (per CriticalAlert)
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3:8b

# Qdrant
QDRANT_HOST=http://localhost:6333
```

### Configurazione Intervalli (da Dashboard)

1. Vai a **Settings** nella dashboard
2. Imposta l'intervallo per ogni agente
3. Clicca **Save All Intervals**

Gli intervalli vengono salvati in MongoDB e applicati al riavvio dell'agente.

---

## 🖥️ Dashboard Web

### Sezioni

| Sezione | Descrizione |
|---------|-------------|
| **Dashboard** | Overview con statistiche |
| **Inventory** | Lista database con status |
| **Alerts** | Storico alert con severità |
| **AI Chat** | Assistente AI conversazionale |
| **Mailbox** | Archivio email inviate |
| **Explorer** | Visualizzazione JSON/Graph MongoDB |
| **Agents** | Controllo agenti con RAG status |
| **Settings** | Configurazione intervalli |

### Funzionalità Agents Panel

- **Start Agent**: Esegue l'agente una volta e mostra output
- **Sync CheckMK**: Sincronizza metriche esterne
- **Run AI Analysis**: Analizza alert forensici con RAG
- **Refresh Status**: Aggiorna stato agenti

---

## 🔧 Troubleshooting

### MongoDB non raggiungibile

```powershell
# Verifica container
docker ps | findstr mongodb

# Riavvia
docker restart nexi-mongodb
```

### Ollama non risponde

```powershell
# Verifica container
docker logs nexi-ollama

# Riavvia con GPU
.\restart_ollama_gpu.ps1
```

### Email non inviate

1. Verifica `SMTP_USER` e `SMTP_PASSWORD` nel `.env`
2. Per Gmail, usa una **App Password** (non la password normale)
3. Controlla la cartella `emails/` per le copie locali

### Agente non rileva database

1. Verifica che i container abbiano label `db.type`
2. Verifica che il gateway sia UP:
   ```powershell
   docker ps | findstr gw-
   ```

---

## 📞 Supporto

Per problemi o domande:
- Apri una Issue su GitHub
- Contatta: MOHAMED.D.N.2002@GMAIL.COM

---

## 📜 Licenza

Proprietario - Nexi S.p.A.
