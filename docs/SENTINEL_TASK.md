# Intelligent DBA Sentinel System - Task Tracker

## Overview
Design and implement a comprehensive AI-powered DBA monitoring system that integrates static code analysis, real-time metrics, predictive modeling, and multi-agent remediation workflows.

---

## Phase 1: Repository Knowledge Ingestion (Static Analysis) ✅
- [x] Create `SentinelRAGIngester` class to scan repository for SQL scripts, stored procedures, and config files
- [x] Index into Qdrant vector database with semantic embeddings
- [x] Build knowledge base of standard operating procedures from existing scripts

---

## Phase 2: Data Ingestion Pipeline ✅
- [x] Create `OEM_Collector` agent to fetch metrics from Oracle Enterprise Manager REST API
- [x] Extend `CheckMK_Collector` to handle legacy 1.5.x instances via Livestatus *(Already exists)*
- [x] Create `VictoriaMetrics Client` for writing/querying time-series data
- [ ] Define Grafana dashboard provisioning for real-time visualization

---

## Phase 3: Predictive & Remediation Engine (Core MAS) ✅
### A. Predictor Agent
- [x] Create `PredictorAgent` class with time-series forecasting (ARIMA/Prophet)
- [x] Implement anomaly detection for OOM, lock contention, storage exhaustion
- [x] Output probabilistic alerts with confidence scores

### B. Verifier Agent
- [x] Create `VerifierAgent` class using LLM for decision-making
- [x] Compare predictions against real-time database status
- [x] Classify issues as REAL/CRITICAL or FALSE_ALARM

### C. Action Workflow
- [x] Extend `EmailSender` with templated urgent/status report emails
- [x] Integrate with repository knowledge base for procedural fixes *(RAG lookup integrated)*
- [x] Wire into LangGraph workflow for full automation

---

## Phase 4: Integration & Testing ✅
- [x] Wire all components into existing API gateway
  - `/action/sentinel` (Core engine)
  - `/action/oem-collect` (Oracle metrics)
  - `/action/rag-ingest` (Knowledge builder)
  - `/sentinel/status` (Health check)
- [x] Test Sentinel workflow end-to-end (**PASSED**)
- [ ] Create Grafana dashboard for predictions visualization

---

## Deliverables
- [x] System Architecture Diagram (Mermaid)
- [x] Tech Stack Recommendation
- [x] Full Python Implementation
