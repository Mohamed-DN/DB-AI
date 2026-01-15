# Collection: gateways

## Scopo del progetto
Store gateway inventory and connectivity metadata.

## Installazione e Setup
Created by gateway provisioning workflows.

## Architettura
Fields include: gateway_id, hostname, region, ssh_port, status, last_seen.

## Utilizzo
db.gateways.find({ status: "UP" })
