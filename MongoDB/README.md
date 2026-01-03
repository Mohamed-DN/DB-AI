# 🗄️ MongoDB CMDB

Package Python per l'interazione con il database CMDB MongoDB.

## 🚀 Configurazione

### 1. Avviare MongoDB (Docker)
```bash
docker-compose up -d
```

### 2. Installare dipendenze
```bash
pip install -r requirements.txt
```

### 3. Configurare variabili ambiente
```bash
cp .env.example .env
# Modificare .env con le proprie impostazioni
```

### 4. Inizializzare il database
```bash
cd scripts
python create_indexes.py    # Crea indici
python seed_sample_data.py  # Inserisce dati di test
python test_connection.py   # Verifica connessione
```

## 📖 Utilizzo

```python
from src.repositories import InventoryRepository, ServiceRepository

# Trovare database
repo = InventoryRepository()
oracle_dbs = repo.find_by_engine("ORACLE")
high_usage = repo.find_with_tablespace_above_threshold(90)

# Ottenere contatto BAO
svc_repo = ServiceRepository()
bao = svc_repo.get_bao_for_database("NZSEP")
```

## 📁 Struttura

| Directory | Contenuto |
|-----------|-----------|
| `src/connection.py` | Connessione MongoDB |
| `src/models/` | Modelli Pydantic |
| `src/repositories/` | Layer di accesso dati |
| `scripts/` | Script di inizializzazione |
| `struttura_mongo/` | Documentazione schemi |

## 🗂️ Collezioni

| Collezione | Descrizione |
|------------|-------------|
| `inventory_databases` | Digital twin dei database |
| `business_services` | Mapping business-tecnico |
| `gateways` | Bastion host SSH |
| `discovery_queue` | Coda Scout → Collector |
| `agent_runs` | Log esecuzione agenti |
| `rag_knowledge_base` | Documenti per RAG |
| `monitoring_alerts` | Alert da Checkmk |
| `baselines` | Baseline prestazioni |
| `compliance_reports` | Report audit giornaliero |
