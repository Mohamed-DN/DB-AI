Ecco la mappa definitiva delle "autostrade" del tuo CMDB.

In MongoDB non esistono le "Foreign Keys" rigide come in SQL, ma esistono i **Link Logici** che noi rendiamo velocissimi grazie agli **Indici**.

Ecco come si collegano le tre collection e gli script pronti per creare gli indici.

### 1. Schema dei Collegamenti (Logical Links)

Il diagramma logico dei dati si basa su questi 3 "ponti":

1. **Business -> DB:** Il servizio punta al DB tramite `db_unique_name`.
2. **DB -> Gateway:** Il DB punta al Gateway tramite `gateway_ref`.
3. **DB -> DB (DR):** Il Primario punta allo Standby tramite `peer_db_unique_name`.

---

### 2. Strategia degli Indici (Performance)

Copia e incolla questi comandi nella tua console MongoDB (o GUI come Compass/NoSQLBooster). Questi indici coprono il 99% delle tue ricerche, incluse quelle per gli array (es. lista nodi o lista PDB).

#### A. Collection: `inventory_databases`

Questa è la collection più interrogata.

```javascript
// 1. CHIAVE PRIMARIA LOGICA (Obbligatoria)
// Garantisce che non ci siano due DB con lo stesso nome univoco nel CMDB.
db.inventory_databases.createIndex(
  { "identity.db_unique_name": 1 }, 
  { unique: true, name: "idx_unique_dbname" }
);

// 2. RICERCA PER HOST (Multikey Index su Array)
// Fondamentale: permette di trovare il DB cercando UNO QUALSIASI dei suoi nodi/IP.
// Se cerchi "host_ip": "10.10.10.1", trovi subito il documento del DB.
db.inventory_databases.createIndex(
  { "nodes.hostname": 1, "nodes.host_ip": 1 },
  { name: "idx_nodes_lookup" }
);

// 3. LINK AL GATEWAY (Per join veloci)
// Serve per dire: "Dammi tutti i DB serviti da dbgec2"
db.inventory_databases.createIndex(
  { "identity.gateway_ref": 1 },
  { name: "idx_gateway_ref" }
);

// 4. RICERCA PDB (Multikey Index su Array)
// Permette di rispondere a: "Su quale container gira il PDB_SALES?"
db.inventory_databases.createIndex(
  { "configuration.oracle_specific.pdbs.name": 1 },
  { name: "idx_pdb_lookup" }
);

// 5. INDICE DI MONITORAGGIO & ALLARMI
// Per dashboard veloci: filtra per tecnologia e stato.
db.inventory_databases.createIndex(
  { "identity.engine": 1, "identity.environment": 1, "storage.last_check": 1 },
  { name: "idx_monitoring_dashboard" }
);

```

#### B. Collection: `business_services`

Qui la query più critica è la "Reverse Lookup" (Dall'incidente al Business).

```javascript
// 1. LINK AL DATABASE (Multikey Index - CRITICO)
// Questo è l'indice "Salva-Vita". Quando cade un DB, usi questo per trovare il BAO.
// Cerca dentro l'array 'technical_mapping'.
db.business_services.createIndex(
  { "technical_mapping.db_unique_name": 1 },
  { name: "idx_tech_mapping_db" }
);

// 2. RICERCA UTENZA/SCHEMA
// "Di chi è l'utenza CRD_OWNER?"
db.business_services.createIndex(
  { "technical_mapping.schemas.schema_name": 1 },
  { name: "idx_schema_owner" }
);

// 3. RICERCA PER ID SERVICE NOW
db.business_services.createIndex(
  { "service_info.service_now_id": 1 },
  { unique: true, name: "idx_snow_id" }
);

```

#### C. Collection: `gateways`

Tabella di lookup per l'infrastruttura.

```javascript
// 1. CHIAVE PRIMARIA (Il nome del Gateway)
// (Nota: _id è indicizzato di default, ma se usi un campo custom:)
// db.gateways.createIndex({ "_id": 1 }); // Già automatico

// 2. RICERCA PER IP PUBBLICO/PRIVATO
db.gateways.createIndex(
  { "info.ip_address": 1 },
  { name: "idx_gw_ip" }
);

// 3. GEOLOCALIZZAZIONE (Per report)
db.gateways.createIndex(
  { "location.country": 1, "location.datacenter": 1 },
  { name: "idx_gw_location" }
);

```

---

### 3. Esempio Pratico: "La Super Query"

Ora che hai gli indici, ecco come MongoDB usa questi "Link" per generare il report completo che volevi mostrare a Marco.

**Scenario:** Vogliamo un report che dica:

* Nome Servizio (da `business_services`)
* Nome DB (da `inventory_databases`)
* Stato Tablespace (da `inventory_databases`)
* IP Gateway (da `gateways`)

Useremo una **Aggregation Pipeline** (la versione Mongo della JOIN SQL).

```javascript
db.business_services.aggregate([
  // 1. Partiamo dai SERVIZI
  { "$unwind": "$technical_mapping" }, // Esplodiamo l'array dei DB collegati

  // 2. JOIN con INVENTORY_DATABASES
  // Usiamo l'indice 'idx_unique_dbname' creato prima
  {
    "$lookup": {
      "from": "inventory_databases",
      "localField": "technical_mapping.db_unique_name", // Campo in Services
      "foreignField": "identity.db_unique_name",        // Campo in DB
      "as": "db_details"
    }
  },
  { "$unwind": "$db_details" }, // Appiattiamo il risultato

  // 3. JOIN con GATEWAYS
  // Usiamo l'indice 'idx_gw_id' (su _id)
  {
    "$lookup": {
      "from": "gateways",
      "localField": "db_details.identity.gateway_ref", // Campo in DB
      "foreignField": "_id",                           // Campo in Gateway
      "as": "gateway_details"
    }
  },
  { "$unwind": "$gateway_details" },

  // 4. PROIEZIONE FINALE (Il Report per Marco)
  {
    "$project": {
      "Servizio": "$service_info.name",
      "BAO": "$contacts.bao.name",
      "Database": "$technical_mapping.db_unique_name",
      "Stato_DB": "$db_details.nodes.status", // Array degli stati
      "Gateway_IP": "$gateway_details.info.ip_address",
      "Tablespace_Alert": {
        // Filtriamo solo i tablespace pieni > 90%
        "$filter": {
          "input": "$db_details.storage.tablespaces",
          "as": "tbs",
          "cond": { "$gte": ["$$tbs.used_pct", 90] }
        }
      }
    }
  }
])

```

Questo chiude il cerchio. Hai:

1. **Dati strutturati** (i 3 JSON).
2. **Velocità** (gli Indici).
3. **Relazioni** (le query di Lookup).

Sei pronto per implementare. Vuoi altro o possiamo considerare il design del CMDB concluso?