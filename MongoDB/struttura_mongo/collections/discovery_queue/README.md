# Collection: discovery_queue

## Scopo del progetto
Queue of discovery tasks and pending scans.

## Installazione e Setup
Created by Scout and backend workflows.

## Architettura
Fields include: target, state, created_at, discovered_at, error.

## Utilizzo
db.discovery_queue.find({ state: "PENDING" })
