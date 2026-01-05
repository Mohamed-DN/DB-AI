# 🧠 Orchestrator - Nexi DBA AI

Il modulo **Orchestrator** contiene tutta la logica AI del sistema.

## 📋 Struttura

```
Orchestrator/
├── src/
│   └── mongo_proxy.py      # Interfaccia MongoDB
├── llm/
│   └── ollama_client.py    # Client Ollama LLM
├── vector_db/
│   └── qdrant_client.py    # Client Qdrant Vector DB
├── rag/
│   └── rag_pipeline.py     # Pipeline RAG completa
└── config/
    └── llm_config.py       # Configurazione modelli
```

---

## 🔌 MongoProxy

**File**: `src/mongo_proxy.py`

Interfaccia unificata per MongoDB che evita dipendenze dirette da `pymongo`.

**Caratteristiche**:
- Esegue comandi via `mongosh` (CLI ufficiale MongoDB)
- Parsing automatico JSON dei risultati
- Gestione errori robusta

**Uso**:
```python
from Orchestrator.src.mongo_proxy import MongoProxy

mongo = MongoProxy()

# Query
result = mongo.execute_eval("db.inventory_databases.find().toArray()")

# Insert
mongo.insert_alert({
    "type": "DB_DOWN",
    "db_unique_name": "PROD1",
    "message": "Database non raggiungibile"
})
```

---

## 🤖 OllamaClient

**File**: `llm/ollama_client.py`

Client per interagire con Ollama (LLM locale).

**Caratteristiche**:
- Generazione testo (`generate`)
- Chat multi-turno (`chat`)
- Analisi errori database (`analyze_db_error`)
- Health check e lista modelli

**Uso**:
```python
from Orchestrator.llm.ollama_client import OllamaClient

client = OllamaClient()

# Verifica connessione
if client.health_check():
    print("Ollama OK")

# Generazione
response = client.generate("Spiega ORA-00600")
print(response["response"])

# Analisi errore
diagnosis = client.analyze_db_error(
    "ORA-00600: internal error code",
    context="Checkpoint in corso"
)
```

**Configurazione**:
```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3:8b
```

---

## 🔍 QdrantClient

**File**: `vector_db/qdrant_client.py`

Client per ricerca semantica con Qdrant.

**Caratteristiche**:
- Gestione collezioni
- Upsert documenti con embedding
- Ricerca per similarità
- Ricerca per codice errore

**Uso**:
```python
from Orchestrator.vector_db.qdrant_client import QdrantClient, generate_simple_embedding

client = QdrantClient()

# Crea collezione
client.create_collection("nexi_knowledge_base")

# Inserisci documento
doc = {
    "content": "ORA-00600 indica errore interno...",
    "source": "Oracle KB"
}
embedding = generate_simple_embedding(doc["content"])
client.upsert_documents([doc], [embedding])

# Cerca
query_embedding = generate_simple_embedding("internal error oracle")
results = client.search(query_embedding, limit=5)
```

---

## 🧪 RAGPipeline

**File**: `rag/rag_pipeline.py`

Pipeline completa Retrieval-Augmented Generation.

**Flusso**:
```
User Query → Embed → Search Qdrant → Retrieve Docs → Augment Prompt → Ollama → Response
```

**Caratteristiche**:
- Knowledge base pre-popolata con runbook Oracle
- Diagnosi errori con contesto log
- Confidence score basato su retrieval quality

**Uso**:
```python
from Orchestrator.rag.rag_pipeline import RAGPipeline

rag = RAGPipeline()

# Seed knowledge base (una volta)
rag.seed_knowledge_base()

# Diagnosi errore
result = rag.diagnose_error(
    error_line="ORA-00600: internal error code, arguments: [kghstack1]",
    log_context=["Line 1", "Line 2", "Line 3"],
    additional_info={"db_name": "PROD1", "engine": "ORACLE"}
)

print(f"Diagnosis: {result['diagnosis']}")
print(f"Confidence: {result['confidence']}")
print(f"Sources: {result['retrieved_docs']}")
```

**Knowledge Base inclusa**:
- ORA-00600 (Internal Error)
- ORA-01555 (Snapshot Too Old)
- ORA-04031 (Shared Memory)
- DataGuard Lag Troubleshooting
- RMAN Backup Failure Guide

---

## ⚙️ Configurazione LLM

**File**: `config/llm_config.py`

Configurazione centralizzata per modelli LLM.

**Modelli disponibili**:
| Modello | Dimensione | Uso |
|---------|------------|-----|
| `llama3:8b` | 8B | Default, veloce |
| `qwen2.5:14b` | 14B | Raccomandato, migliore |
| `codellama:13b` | 13B | SQL e codice |
| `deepseek-r1:14b` | 14B | Ragionamento complesso |

**Switch modello da dashboard**:
1. Vai a **AI Chat**
2. Seleziona modello dal dropdown
3. Il cambio è immediato
