# RAG Knowledge Base Collection

Contiene i documenti chunked e i loro embedding per il sistema RAG.

## Scopo

Il **RAG Orchestrator** usa questa collection per:
1. Ricercare documenti rilevanti (tramite vector search o text search).
2. Fornire contesto all'AI prima di generare una risposta.

## Tipi di Documenti

- `README`: Documentazione di progetto.
- `RUNBOOK`: Procedure operative.
- `SQL_SCRIPT`: Script SQL con commenti.
- `POLICY`: Policy aziendali.
- `ARCHITECTURE_DOC`: Documenti di architettura (come questo!).

## Indici

```javascript
// Text search index
db.rag_knowledge_base.createIndex({ "text_chunk": "text" }, { name: "idx_text_search" });

// Metadata filtering
db.rag_knowledge_base.createIndex({ "metadata.db_engines": 1, "metadata.tags": 1 }, { name: "idx_metadata_filter" });

// Source lookup
db.rag_knowledge_base.createIndex({ "source_path": 1, "chunk_index": 1 }, { unique: true, name: "idx_unique_chunk" });
```

## Vector Search (Atlas)

Se usi MongoDB Atlas, puoi creare un indice vettoriale per gli embedding:

```json
{
  "mappings": {
    "dynamic": true,
    "fields": {
      "embedding": {
        "type": "knnVector",
        "dimensions": 768,
        "similarity": "cosine"
      }
    }
  }
}
```
