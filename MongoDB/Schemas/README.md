# MongoDB CMDB Schema Documentation

This directory documents the metadata structure for the AI-Driven CMDB.

## Collections

### Core CMDB
- **inventory_databases/**: Digital twin of each managed database.
- **business_services/**: Business-to-technical mapping (BAO, contacts).
- **gateways/**: SSH bastion hosts for access.

### SADA Agent Support
- **discovery_queue/**: Work queue for Scout → Collector communication.
- **agent_runs/**: Execution audit log for SADA agents.

### RAG System
- **rag_knowledge_base/**: Chunked documents and embeddings for the AI RAG layer.
