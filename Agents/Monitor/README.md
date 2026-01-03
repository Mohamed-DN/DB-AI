# SADA-MONITOR Agent

The **Monitor** agent syncs alerts from Checkmk to the CMDB.

## Functions

1. **API Polling**: Queries Checkmk REST API for service states.
2. **CMDB Linking**: Matches alerts to `db_unique_name` in `inventory_databases`.
3. **Persistence**: Writes/updates `monitoring_alerts` collection.

## Frequency
- **Every 1 minute** for critical alerts.
- **Every 5 minutes** for warning/ok states.

## Configuration

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

## Key Endpoints Used

| Endpoint                          | Purpose             |
| --------------------------------- | ------------------- |
| `GET /domain-types/host/...`      | List managed hosts  |
| `GET /domain-types/service/...`   | Get service states  |
| `GET .../show_service_metrics`    | Get metrics data    |
