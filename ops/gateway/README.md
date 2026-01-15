# Gateway

> SSH gateways and Network Services configuration.

## Purpose

Gateways act as jump hosts to reach databases in isolated networks, allowing the central application to access distributed resources securely.

```
User → Gateway → Database
```

## 📂 Directory Contents

| Directory/File | Description |
|----------------|-------------|
| **`redis_config/`** | Configuration files for the Redis instance used by the Gateway or caching layer. |
| **`README.md`** | This file. |

## 🌍 V2 Gateways

| Gateway | Location | Accessible DBs |
|---------|----------|----------------|
| **nexi-gw-milano2** | Milan, Italy | `pg-milano-*` |
| **nexi-gw-bratislava2** | Bratislava, Slovakia | `pg-bratislava-*` |
| **nexi-gw-cairo2** | Cairo, Egypt | `oracle-cairo-*` |

## ⚙️ Usage

- Gateway info is stored in the MongoDB `gateways` collection.
- The `Scout` agent uses the `GATEWAY_SUFFIX` environment variable to identify and connect through V2 gateways.
