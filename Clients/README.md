# Clients

## Scopo del progetto
Placeholders for external clients that integrate with the backend API.

## Installazione e Setup
No extra setup. See README.md.

## Architettura
Clients call FastAPI endpoints under /api and consume JSON responses.

## Utilizzo
Examples:
curl http://localhost:9000/api/inventory
curl -X POST http://localhost:9000/api/action/scan
