# Baselines Collection

Stores performance baselines for comparison and anomaly detection.

## Purpose
- Track normal operating metrics
- Detect performance degradation
- Capacity trending

## Indexes

```javascript
db.baselines.createIndex({ "db_unique_name": 1, "baseline_date": -1 }, { name: "idx_db_baseline" });
db.baselines.createIndex({ "type": 1 }, { name: "idx_baseline_type" });
```
