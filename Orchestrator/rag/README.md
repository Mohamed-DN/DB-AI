# RAG Pipeline

## Scopo del progetto
Combine retrieval from Qdrant with prompts for LLM responses.

## Installazione e Setup
Qdrant must be running. Configure QDRANT_HOST.

## Architettura
- rag/ for ingestion and retrieval steps
- vector_db/ for storage and search
- knowledge sources from MongoDB and docs

## Utilizzo
Used by backend and agents to enrich alerts and chat responses.
