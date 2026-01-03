# Orchestrator Layer (Layer 3)

The brain of the DBA AI system. Coordinates all AI processing and decision-making.

## Components

| Directory | Purpose |
|-----------|---------|
| `rag/` | Retrieval Augmented Generation pipeline |
| `llm/` | Local LLM integration (Ollama) |
| `vector_db/` | Qdrant configuration for embeddings |
| `modules/` | AI behavior modules |

## AI Modules

### THE ARCHITECTURE
System design and topology understanding. Knows how databases relate to each other.

### THE WATCHER
Proactive monitoring. Predicts problems before they occur using patterns and ML.

### THE TUNING
Performance optimization. Suggests and applies tuning configurations.

## Data Sources

- **MongoDB**: CMDB, documents, prompts
- **Qdrant**: Vector embeddings for semantic search
- **Checkmk**: Real-time monitoring alerts
