# 📡 Monitor Agent

Agente per la sincronizzazione degli alert da Checkmk al CMDB.

## 📋 Funzionalità

1. **Polling API**: Interroga l'API REST di Checkmk per gli stati dei servizi
2. **Link CMDB**: Collega gli alert al `db_unique_name` in `inventory_databases`
3. **Persistenza**: Scrive/aggiorna la collezione `monitoring_alerts`

## ⏱️ Frequenza
- **Ogni 1 minuto** per alert critici
- **Ogni 5 minuti** per stati warning/ok

## ⚙️ Configurazione

```yaml
# config/checkmk.yaml
checkmk:
  server: "https://checkmk.company.local/mysite"
  username: "automation_user"
  secret: "${CHECKMK_SECRET}"
  
filters:
  host_labels: "cmdb:managed"
  service_patterns:
    - "Oracle*"
    - "Postgres*"
    - "Tablespace*"
```

## 🔗 Endpoint Utilizzati

| Endpoint | Scopo |
|----------|-------|
| `GET /domain-types/host/...` | Lista host gestiti |
| `GET /domain-types/service/...` | Stati servizi |
| `GET .../show_service_metrics` | Dati metriche |
