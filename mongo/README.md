# 🍃 MongoDB Infrastructure

## 🎯 Scopo
Contiene tutto il necessario per la gestione del database MongoDB: definizioni di schemi, script di manutenzione, seed data e configurazioni di deployment.

## 📂 File Manifest
- **`schemas/`**: (Directory) Definizioni JSON e Python degli schemi delle collection (es. Inventory, Alerts).
- **`scripts/`**: (Directory) Utility per la pulizia, la correzione dei dati e la migrazione da Oracle.
- **`seeds/`**: (Directory) Script di popolamento iniziale del database per ambienti di test.
- **`docker-compose.yml`**: Configurazione Docker per il servizio MongoDB locale.

## 🔗 Connessioni
- **Da `api_agents`**: Gli agenti leggono la configurazione e scrivono metriche.
- **Da `web`**: Il backend interroga queste collection per mostrare dati nella dashboard.
- **Da `orchestrator`**: RAG e LLM usano i dati qui contenuti come contesto.
