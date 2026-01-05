# Business Services Collection

Mapping business-to-technical: collega servizi aziendali ai database.

## Scopo

- **Contatti**: Chi chiamare per un servizio (BAO, DL, reperibilità)
- **Ownership**: Quale team è responsabile
- **Schema mapping**: Quali utenze/schemi appartengono a quale servizio

## Campi Principali

| Campo | Descrizione |
|-------|-------------|
| `service_info` | Nome servizio, ID ServiceNow, stato |
| `contacts.bao` | Business Application Owner (nome + email) |
| `contacts.dl_team` | Distribution list operativa |
| `contacts.reperibilita_number` | Numero emergenze |
| `technical_mapping` | Array di `{db_unique_name, schemas[]}` |

## Relazioni

Ogni `technical_mapping.db_unique_name` è una FK verso `inventory_databases.identity.db_unique_name`.

## Indici

```javascript
// Lookup per database
db.business_services.createIndex(
  { "technical_mapping.db_unique_name": 1 },
  { name: "idx_tech_mapping_db" }
);

// Lookup per ServiceNow ID
db.business_services.createIndex(
  { "service_info.service_now_id": 1 },
  { unique: true, name: "idx_snow_id" }
);
```
