# Gateways Collection

Bastion host SSH che fungono da ponte per accedere ai database.

## Scopo

- **Routing**: Definire quale gateway usare per raggiungere un database
- **Topologia**: Mappare quale datacenter serve quali host
- **Monitoraggio**: Tracciare stato e raggiungibilità

## Campi Principali

| Campo | Descrizione |
|-------|-------------|
| `_id` | ID univoco gateway (es. `dbgec2`) |
| `location` | Paese, città, datacenter |
| `info` | Hostname, IP, OS, hardware |
| `network` | Porte aperte, stato |
| `reachability` | Host e database accessibili |

## Indici

```javascript
// Lookup per hostname
db.gateways.createIndex(
  { "info.hostname": 1 },
  { unique: true, name: "idx_gw_hostname" }
);

// Lookup per datacenter
db.gateways.createIndex(
  { "location.datacenter": 1 },
  { name: "idx_gw_datacenter" }
);
```
