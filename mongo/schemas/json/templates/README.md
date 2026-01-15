# JSON Templates per Agente di Estrazione CMDB

Questa directory contiene i **template JSON** che l'Agente di Estrazione deve usare come riferimento per la struttura dei documenti.

## File Disponibili

| File | Tecnologia | Descrizione |
|------|------------|-------------|
| `oracle_template.json` | Oracle | Template per database Oracle (RAC, Dataguard, SCAN/VIP) |
| `postgresql_template.json` | PostgreSQL | Template per cluster Postgres (Patroni, Replication Slots) |

## Direttiva Fondamentale (Schema Evolution)

> **L'Agente ha piena autonomia di modificare la struttura del documento JSON dinamicamente.**

Se durante la scansione vengono rilevate configurazioni complesse (più interfacce di rete, parametri custom, topologie cluster ibride), l'Agente **DEVE** adattare il JSON aggiungendo campi o annidando oggetti per catturare la realtà senza perdere dati.

**La fedeltà del dato vince sulla rigidità dello schema.**

## Regole di Naming (File System)

### Struttura Directory
```
ROOT_PATH / {TECNOLOGIA} / {AMBIENTE} / {YYYY-MM-DD} /
```
- Esempio Oracle: `/mnt/cmdb_ingest/oracle/integration/2026-01-13/`
- Esempio Postgres: `/mnt/cmdb_ingest/postgresql/production/2026-01-13/`

### Naming Convention
```
{DB_UNIQUE_NAME}_{HOSTNAME}_{TIMESTAMP_EPOCH}.json
```
- Esempio: `CAUNRAZ2I_maamdba2ucrti01_1736769000.json`

### Gestione Aggiornamenti
- **Immutabilità**: L'agente NON sovrascrive mai i file
- **Pipeline**: Il loader sposta i file in `processed/` o `failed/` dopo l'elaborazione

## Campi Critici (Array Obbligatori)

### Oracle (RAC)
- `network.cluster_interconnect.scan_ips` → **Array** di 3 IP
- `network.cluster_interconnect.node_vips` → **Array** di N IP (1 per nodo)

### PostgreSQL
- `replication_ha.replication_slots` → **Array** di oggetti slot
- `storage_info.tablespaces` → **Array** di oggetti tablespace
- `extensions_installed` → **Array** di oggetti estensione
