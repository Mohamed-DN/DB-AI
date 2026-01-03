# Monitoring Alerts Collection

Contiene gli alert sincronizzati da Checkmk, collegati al CMDB.

## Scopo

- **Correlazione**: Collegare alert di monitoring ai database nel CMDB.
- **Storico**: Tracciare l'evoluzione degli alert.
- **AI Analysis**: Fornire contesto all'AI per diagnosi.

## Indici

```javascript
// Query per host e stato
db.monitoring_alerts.createIndex(
  { "host_name": 1, "state": 1 },
  { name: "idx_host_state" }
);

// Link al CMDB
db.monitoring_alerts.createIndex(
  { "cmdb_db_ref": 1 },
  { name: "idx_cmdb_link" }
);

// Alert attivi (non acknowledged)
db.monitoring_alerts.createIndex(
  { "state": 1, "acknowledged": 1, "last_check": -1 },
  { name: "idx_active_alerts" }
);

// Unique constraint
db.monitoring_alerts.createIndex(
  { "source": 1, "host_name": 1, "service_name": 1 },
  { unique: true, name: "idx_unique_alert" }
);
```
