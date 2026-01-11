# Gateway

> SSH gateways for secure database access.

## Purpose

Gateways act as jump hosts to reach databases in isolated networks:

```
User → Gateway → Database
```

## V2 Gateways

| Gateway | Location | Accessible DBs |
|---------|----------|----------------|
| nexi-gw-milano2 | Milan | pg-milano-* |
| nexi-gw-bratislava2 | Bratislava | pg-bratislava-* |
| nexi-gw-cairo2 | Cairo | oracle-cairo-* |

## Configuration

Gateway info is stored in MongoDB `gateways` collection.

Scout agent uses `GATEWAY_SUFFIX` env var to find V2 gateways.
