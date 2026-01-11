# Orchestrator

> LLM and RAG pipeline for AI-powered chat and analysis.

## Components

```
Orchestrator/
├── src/
│   ├── mongo_proxy.py   # MongoDB via Docker CLI
│   └── ...
├── rag/                 # RAG pipeline (Qdrant)
└── config/              # LLM settings
```

## LLM Configuration

Default model: `qwen2.5:7b` via Ollama

```bash
# Test Ollama
curl http://localhost:12434/api/generate -d '{"model":"qwen2.5:7b","prompt":"Hello"}'
```

## MongoProxy

When direct PyMongo fails, use `MongoProxy` which wraps `docker exec mongosh`:

```python
from Orchestrator.src.mongo_proxy import MongoProxy
mongo = MongoProxy()
result = mongo.execute_eval("db.inventory_databases.find().toArray()")
```

## See Also
- [directives/ai_chat.md](../directives/ai_chat.md) - Chat directive
