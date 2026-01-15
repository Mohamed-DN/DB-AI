# 🗄️ Qdrant Vectors Basics

> **Context**: For the `Orchestrator` RAG pipeline.

## 🧬 Concepts
- **Embedding**: Converting text to a number array (vector). We use `all-MiniLM-L6-v2` (384 dimensions).
- **Cosine Similarity**: How we measure distance between query and document.

## 🛠️ API Interaction (REST)
Qdrant exposes a REST API on port `6333`.

### Health Check
```bash
curl http://localhost:6333/healthz
```

### List Collections
```bash
curl http://localhost:6333/collections
```

### Search (Python Client)
```python
from qdrant_client import QdrantClient

client = QdrantClient("localhost", port=6333)
hits = client.search(
    collection_name="wiki_docs",
    query_vector=[0.1, 0.2, ...], # 384 floats
    limit=3
)
```

## ⚠️ Common Issues
- **Dimension Mismatch**: Trying to insert a 768-dim vector into a 384-dim collection.
- **Payload Too Large**: Storing entire megabytes of text in payload. (Store chunks < 1000 chars).
