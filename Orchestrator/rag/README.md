# RAG Pipeline

Retrieval Augmented Generation for context-aware AI responses.

## Flow

1. **Query** → User asks a question
2. **Retrieve** → Search Qdrant for relevant documents
3. **Augment** → Combine docs with CMDB context
4. **Generate** → LLM produces response

## Data Sources for RAG

- Runbooks and procedures
- SQL scripts with comments
- Architecture documentation
- Historical incidents
