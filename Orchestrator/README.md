# Orchestrator

## Scopo del progetto
Coordinates LLM and RAG workflows and provides analysis utilities.

## Installazione e Setup
Ensure Ollama and Qdrant are running. Configure OLLAMA_HOST and QDRANT_HOST.

## Architettura
- config/llm_config.py: model catalog and defaults
- llm/: Ollama client utilities
- vector_db/: Qdrant client utilities
- rag/: retrieval and prompt assembly
- src/mongo_proxy.py: MongoDB access via Docker

## Utilizzo
Used by backend endpoints and agents for AI analysis and chat.
