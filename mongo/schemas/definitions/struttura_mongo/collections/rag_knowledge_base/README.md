# Collection: rag_knowledge_base

## Scopo del progetto
Store documents and embeddings used by the RAG pipeline.

## Installazione e Setup
Created by ingestion pipelines.

## Architettura
Fields include: source, title, content, tags, embedding_id, created_at.

## Utilizzo
db.rag_knowledge_base.find({ tags: "oracle" }).limit(10)
