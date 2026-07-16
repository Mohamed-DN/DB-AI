# 🍃 MongoDB Best Practices

> **Context**: For the `mongo` layer of M-DN DBA.

## 🏗️ Schema Design
- **Embed vs Reference**: Embed when data is accessed together (1:Few). Reference when data grows indefinitely (1:Many).
- **Indexes**: Every query should use an index. Use `explain()` to verify.

## ⚡ Performance Commands

### Check Current Operations
```javascript
db.currentOp({ "active": true, "secs_running": { "$gt": 3 } })
```

### Collection Stats
```javascript
db.inventory_databases.stats()
```

### Create Index (Background)
```javascript
db.inventory_databases.createIndex({ "identity.db_unique_name": 1 }, { background: true })
```

## 🛡️ Backup & Restore
- **Backup**: `mongodump --uri="mongodb://..." --out=/backup/`
- **Restore**: `mongorestore --uri="mongodb://..." /backup/`

## 🤖 M-DN Architecture Notes
- We use **Time Series Collections** for metrics (`metrics_cpu`, `metrics_ram`) introduced in Mongo 5.0.
- `inventory_databases` uses an "Attribute Pattern" for flexible schema support across Oracle/Postgres.
