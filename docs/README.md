# 📚 Documentation

## 🎯 Scopo
Repository centrale per tutta la documentazione non legata direttamente al codice sorgente, incluse le direttive operative per l'AI e i diagrammi architetturali.

## 📂 File Manifest
- **`architecture/`**: (Directory) Documenti di alto livello sull'architettura, specifiche di ingestione dati e pipeline.
- **`directives/`**: (Directory) "SOP" (Standard Operating Procedures) che guidano il comportamento degli agenti AI (es. "Come diagnosticare un errore ORA-00600").

## 🔗 Connessioni
- **Per `orchestrator`**: Le direttive vengono caricate nel Vector DB (Qdrant) per essere richiamate tramite RAG durante il problem solving.
