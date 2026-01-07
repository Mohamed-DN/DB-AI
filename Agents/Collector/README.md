# 🔬 Collector Agent

Agente per l'estrazione profonda dei dati da database Oracle e PostgreSQL.

## 📋 Funzionalità

- Connessione SSH via Gateway (bastion) obbligatoria
- Estrazione dati Oracle (versione, patch, storage, RAC, DataGuard)
- Estrazione dati sistema (OS, CPU, memoria)
- Trasformazione e aggiornamento CMDB

## 🚀 Configurazione

### 1. Installare dipendenze
```bash
pip install -r requirements.txt
```

### 2. Configurare il gateway
```bash
cp config/config.yaml.example config/config.yaml
# Modificare config.yaml con le credenziali del gateway
```

### 3. Configurare variabili ambiente
```bash
export GATEWAY_HOST="gw-milano.nexi.lab"
export GATEWAY_USER="service_audit"
export GATEWAY_PASSWORD="audit2024"
export MONGO_URI="mongodb://admin:nexi2024@localhost:27017"
```

## 📖 Utilizzo

Tutte le connessioni devono passare dal gateway.

### Raccolta da host specifici
```bash
python main.py --targets host1.local host2.local --gateway gw-milano
```

## 📁 Struttura

```
Collector/
├── main.py                 # Entry point
├── requirements.txt        # Dipendenze
├── config/
│   └── config.yaml.example # Template configurazione
├── src/
│   ├── ssh_connection.py   # Helper Gateway/SSH
│   ├── cmdb_updater.py     # Trasformazione CMDB
│   └── extractors/
│       ├── oracle_extractor.py  # Query SQL Oracle
│       └── system_extractor.py  # Comandi sistema
└── resources/
    └── oracle_scripts/     # Script SQL aggiuntivi
```

## 🔍 Query SQL Eseguite

| Query | Dati Estratti |
|-------|--------------|
| v$database, v$instance | Info database |
| dba_registry_sqlpatch | Patch installate |
| v$asm_diskgroup | Diskgroup ASM |
| dba_tablespace_usage_metrics | Tablespace |
| gv$instance | Nodi RAC |
| v$archive_dest_status | Stato Data Guard |
| dba_feature_usage_statistics | Opzioni licenza |

## 🧪 Test con Ambiente Docker

```bash
# Avviare l'ambiente lab
cd ../../docker-lab
docker-compose up -d

# Testare connessione al gateway
ssh -p 2221 service_audit@localhost

# Eseguire collector su database di test
python main.py --targets pg-milano-prod.nexi.lab --gateway gw-milano
```
