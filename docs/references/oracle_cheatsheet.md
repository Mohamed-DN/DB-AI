# 🏛️ Oracle Database Cheatsheet for AI Agents

> **Context**: Useful commands for the `Scout` and `Collector` agents when interacting with Oracle containers.

## 🔑 Key Concepts
- **SID**: System Identifier (e.g., `JUPITER`, `XE`).
- **PDB**: Pluggable Database (Modern Oracle).
- **RMAN**: Recovery Manager (Backups).
- **Redo Logs**: Transaction logs (Critical for CDC).

## 🛠️ Common SQL Commands

### Check Instance Status
```sql
SELECT instance_name, status, version FROM v$instance;
```

### Check Tablespace Usage
```sql
SELECT tablespace_name, 
       ROUND(used_space * 8192 / 1024 / 1024, 2) AS used_mb,
       ROUND(tablespace_size * 8192 / 1024 / 1024, 2) AS size_mb
FROM dba_tablespace_usage_metrics;
```

### Find Locking Sessions
```sql
SELECT s.sid, s.serial#, s.username, s.program, l.type
FROM v$session s, v$lock l
WHERE s.sid = l.sid AND l.block = 1;
```

### Kill a Session
```sql
ALTER SYSTEM KILL SESSION 'sid,serial#';
```

## 🤖 Agent Specifics
- **Scout**: Uses `lsnrctl status` to find services.
- **Watcher**: Greps `alert.log` for `ORA-` errors.
