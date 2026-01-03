# Vector Database (Qdrant)

Qdrant is used for storing and searching embeddings for the RAG system.

## Why Qdrant?

- High performance vector search
- Filtering support (by metadata)
- Memory persistence
- REST/gRPC APIs

## Configuration

```yaml
qdrant:
  host: "localhost"
  port: 6333
  collection: "dba_knowledge"
  vector_size: 768
  distance: "Cosine"
```

## Docker

```bash
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
```

## Collections

| Collection | Purpose |
|------------|---------|
| `dba_knowledge` | Runbooks, docs, procedures |
| `sql_scripts` | Oracle/Postgres scripts |
| `incidents` | Historical incident data |
