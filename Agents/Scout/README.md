# 🔭 Scout Agent

Agente leggero per la scoperta di nuovi database nell'infrastruttura.

## 📋 Funzionalità

1. **Scansione Processi**: Rileva processi Oracle (pmon), Postgres, MySQL
2. **Classificazione AI**: Identifica tipologia e ambiente
3. **Persistenza**: Scrive i target scoperti in `discovery_queue`

## ⏱️ Frequenza
- **Ogni 5 minuti** scansione di tutti gli host

## 🔍 Processi Rilevati

| Engine | Processo |
|--------|----------|
| Oracle | `ora_pmon_*`, `tnslsnr` |
| Postgres | `postgres`, `postmaster` |
| MySQL | `mysqld` |

## 📤 Output

Ogni database scoperto viene inserito nella coda:
```json
{
  "target_host": "host.nexi.local",
  "discovered_service": "ora_pmon_NZSEP",
  "engine_detected": "ORACLE",
  "status": "PENDING"
}
```
