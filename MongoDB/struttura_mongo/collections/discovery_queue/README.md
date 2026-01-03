# Discovery Queue Collection

Coda di lavoro per i target scoperti da SADA-SCOUT.

## Flusso

1. **Scout** trova un nuovo processo DB → scrive documento con `status: PENDING`.
2. **Collector** legge i pending → cambia status a `PROCESSING`.
3. Collector completa → cambia status a `COMPLETED` o `FAILED`.

## Indici

```javascript
db.discovery_queue.createIndex({ "status": 1, "discovered_at": 1 }, { name: "idx_pending_queue" });
db.discovery_queue.createIndex({ "target_host": 1, "discovered_service": 1 }, { unique: true, name: "idx_unique_target" });
```
