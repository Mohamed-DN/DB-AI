# 📊 MongoDB - Schema CMDB

Questa directory contiene gli schemi e script per il database MongoDB.

## 📋 Collezioni

### inventory_databases

**Descrizione**: Inventario completo di tutti i database gestiti.

**Schema principale**:
```json
{
  "_id": "ObjectId",
  "identity": {
    "db_name": "nexi-pg-milano-prod",
    "db_unique_name": "NEXI-PG-MILANO-PROD",
    "engine": "POSTGRES",
    "version": "15.0",
    "host": "nexi-pg-milano-prod",
    "port": 5432
  },
  "location": {
    "datacenter": "Milano",
    "gateway": "gw-milano",
    "env": "PROD"
  },
  "contacts": {
    "dba_email": "dba-team@nexi.com",
    "business_owner": "payments-team"
  },
  "state": {
    "status": "UP",
    "last_seen": "2026-01-05T18:00:00Z"
  },
  "deep_observability": {
    "oracle_internals": {
      "tablespaces": [...],
      "asm_diskgroups": [...],
      "fra_usage_pct": 45
    },
    "data_protection": {
      "rman_last_backup": "2026-01-05T02:00:00Z",
      "dataguard_lag_seconds": 3
    },
    "performance_metrics": {
      "cpu_percent": 35,
      "active_sessions": 12,
      "blocking_sessions": 0
    },
    "external_metrics": {
      "checkmk": {
        "host_state": "OK",
        "cpu_util": 35,
        "memory_util": 60,
        "last_sync": "2026-01-05T18:00:00Z"
      }
    }
  }
}
```

---

### monitoring_alerts

**Descrizione**: Alert generati dagli agenti.

**Tipi alert**:
- `DB_DOWN` - Database non raggiungibile
- `DB_RECOVERY` - Database tornato online
- `ASSET_MISSING` - Database non rilevato in Docker
- `DB_FORENSICS` - Errore critico rilevato nei log

**Schema**:
```json
{
  "_id": "ObjectId",
  "type": "DB_DOWN",
  "state": "CRITICAL",
  "db_unique_name": "NEXI-ORACLE-CAIRO-PRIMARY",
  "message": "Gateway gw-cairo is DOWN",
  "timestamp": "2026-01-05T17:30:00Z",
  "processed": false,
  "ai_analysis": {
    "diagnosis": "Il gateway è probabilmente offline...",
    "confidence": 0.85,
    "sources_used": ["Oracle KB", "DBA Playbook"],
    "analyzed_at": "2026-01-05T17:31:00Z"
  }
}
```

---

### system_config

**Descrizione**: Configurazione del sistema.

**Chiavi**:
```json
{ "key": "scout_interval", "value": 60 }
{ "key": "criticalalert_interval", "value": 30 }
{ "key": "watcher_interval", "value": 10 }
{ "key": "forensicanalyzer_interval", "value": 30 }
{ "key": "checkmk_bridge_interval", "value": 60 }
{ "key": "collector_interval", "value": 30 }
{ "key": "global_status", "value": "RUNNING" }
```

---

### gateways

**Descrizione**: Mappa gateway per datacenter.

```json
{
  "name": "gw-cairo",
  "datacenter": "Cairo",
  "container": "nexi-gw-cairo",
  "databases": ["NEXI-ORACLE-CAIRO-PRIMARY", "NEXI-ORACLE-CAIRO-REPLICA"]
}
```

---

## 🔧 Scripts

| Script | Descrizione |
|--------|-------------|
| `scripts/create_indexes.py` | Crea indici per performance |
| `scripts/seed_sample_data.py` | Popola dati di esempio |
| `scripts/update_email_address.py` | Aggiorna email contatti |
| `scripts/check_missing_dbs.py` | Verifica database mancanti |

---

## 📝 Accesso Diretto

### Via mongosh

```powershell
docker exec -it nexi-mongodb mongosh nexi_cmdb
```

### Query utili

```javascript
// Lista database
db.inventory_databases.find({}, {"identity.db_unique_name": 1})

// Alert non processati
db.monitoring_alerts.find({processed: false})

// Configurazione
db.system_config.find()
```

### Via Mongo Express

Vai a: **http://localhost:8081**

---

## 🔄 Backup/Restore

### Backup

```powershell
docker exec nexi-mongodb mongodump --db nexi_cmdb --out /backup
docker cp nexi-mongodb:/backup ./backup
```

### Restore

```powershell
docker cp ./backup nexi-mongodb:/backup
docker exec nexi-mongodb mongorestore --db nexi_cmdb /backup/nexi_cmdb
```
