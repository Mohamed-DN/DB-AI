# 🧠 Orchestrator (AI Core)

## 🎯 Scopo
Il cervello del sistema. Gestisce il flusso informativo, le pipeline RAG (Retrieval-Augmented Generation) e l'integrazione con i Vector DB.

## 📂 File Manifest
- **`core/`**: (Directory) Logica principale dell'Orchestrator (`main.py`, classi base).
- **`rag/`**: (Directory) Pipeline di ingestion e retrieval dei documenti.
- **`vector_db/`**: (Directory) Client e gestione della connessione con Qdrant.
- **`modules/`**: (Directory) Moduli specializzati (es. Performance Tuning, Capacity Planning) chiamati dall'AI.

## 🔗 Connessioni
- **Verso `llm`**: Chiama i client LLM (Ollama) per generare risposte.
- **Verso `mongo`**: Recupera il contest del sistema (inventario, alert).
- **Da `api_agents`**: Riceve richieste di analisi o chat dal backend API.
