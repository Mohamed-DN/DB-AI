# 🐘 PostgreSQL Tuning & Maintenance

> **Context**: Reference for `Collector` metrics and `DailyAudit`.

## ⚙️ Important Config Parameters (`postgresql.conf`)

| Parameter | Recommended (Web Workload) | Description |
|-----------|----------------------------|-------------|
| `max_connections` | 200 | Limit active sessions to avoid overhead. |
| `shared_buffers` | 25% of RAM | Memory for caching table data. |
| `work_mem` | 16MB | Memory per sort operation. |
| `maintenance_work_mem` | 1GB | Memory for VACUUM/INDEX creation. |
| `effective_cache_size` | 75% of RAM | OS cache estimate for query planner. |

## 🔍 Diagnostic Queries

### Active Queries (Long Running)
```sql
SELECT pid, now() - query_start AS duration, query 
FROM pg_stat_activity 
WHERE state != 'idle' 
ORDER BY duration DESC;
```

### Cache Hit Ratio (Should be > 99%)
```sql
SELECT sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio 
FROM pg_statio_user_tables;
```

### Table Bloat (Dead Tuples)
```sql
SELECT relname, n_dead_tup, n_live_tup, 
       (n_dead_tup::float / (n_live_tup + n_dead_tup + 1)::float) * 100 as bloat_pct
FROM pg_stat_user_tables 
WHERE n_dead_tup > 0;
```

## 🧹 Maintenance
- **VACUUM FULL**: Reclaims disk space (Locks table!).
- **ANALYZE**: Updates statistics for query planner.
