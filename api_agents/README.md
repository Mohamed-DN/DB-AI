# 🤖 API & Agents Layer

## 🎯 Scopo
Questa cartella unifica la logica di backend: il gateway API (FastAPI) e i lavoratori autonomi (Agents) che interagiscono con l'infrastruttura.

## 📂 File Manifest
- **`api_gateway/`**: (Directory) Contiene l'applicazione FastAPI (`main.py`) che serve il Frontend ed espone le API REST.
- **`workers/`**: (Directory) Contiene gli agenti autonomi:
    - `Scout`: Discovery dei database.
    - `Collector`: Raccolta metriche.
    - `Watcher`: Analisi log.
- **`shared/`**: (Directory) Librerie condivise (es. `Monitor`) utilizzate da più agenti.

## 🔗 Connessioni
- **Verso `mongo`**: Sia l'API che gli Agenti leggono/scrivono dati su MongoDB (`inventory`, `metrics`).
- **Verso `orchestrator`**: L'API chiama l'Orchestrator per le funzionalità di AI Chat e RAG.
- **Dalla `web`**: L'API Gateway riceve richieste HTTP dal frontend.
