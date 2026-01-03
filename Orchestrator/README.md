# 🧠 Orchestrator

Cervello del sistema DBA AI. Coordina l'elaborazione AI e le decisioni.

## 📋 Componenti

| Directory | Descrizione |
|-----------|-------------|
| `rag/` | Pipeline Retrieval Augmented Generation |
| `llm/` | Integrazione LLM locale (Ollama) |
| `vector_db/` | Configurazione Qdrant per embedding |
| `modules/` | Moduli comportamentali AI |

## 🤖 Moduli AI

### THE ARCHITECTURE
Comprensione della topologia e delle relazioni tra sistemi.
- Conosce le topologie RAC, Data Guard, GoldenGate
- Mappa dipendenze tra database
- Fornisce contesto architetturale

### THE WATCHER
Monitoring proattivo. Predice problemi prima che accadano.
- Analizza trend nelle metriche
- Predice problemi di capacità
- Correla alert tra sistemi

### THE TUNING
Ottimizzazione delle performance.
- Analizza report AWR/ASH
- Suggerisce modifiche parametri
- Identifica query lente

## 📊 Moduli Business

### performance/
- SQL Tuning
- Rilevamento cambio piano
- Analisi bind variables

### capacity/
- Gestione storage
- Policy di retention
- Baseline prestazioni

### best_practices/
- Verifica partitioning
- Analisi indicizzazione
- Validazione ambienti
