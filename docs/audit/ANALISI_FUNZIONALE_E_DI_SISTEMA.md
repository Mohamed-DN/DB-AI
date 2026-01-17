# Documento 1: Analisi Funzionale e di Sistema

## Panoramica Generale
Nexi DBA AI e un sistema di CMDB e operations per database che combina agenti autonomi, un backend API e un frontend dashboard. Il sistema scopre asset DB in ambienti Docker e remoti, aggiorna l'inventario in MongoDB, raccoglie metriche e log, genera alert, e abilita una chat AI con azioni operative supportate da LLM e RAG.

## Flussi e Funzionalita
- 1) Avvio stack: script operativi avviano container, backend e frontend (vedi `ops/scripts/*`).
- 2) Discovery locale: lo Scout scansiona Docker, valida la presenza dei gateway, crea/aggiorna `inventory_databases` e genera alert per nuovi asset o asset mancanti.
- 3) Discovery remota: il Discovery Agent usa gateway/SSH e port scan per trovare DB, arricchisce metadata e inserisce i nuovi asset in MongoDB.
- 4) Provisioning utenti: UserProvisioner crea account AIAUTO sui DB scoperti per abilitare metriche e enrichment.
- 5) Raccolta metriche: Collector legge metriche da container Docker o Oracle remoti e aggiorna `state.metrics` e campi deep.
- 6) Log monitoring: Watcher taila i log e crea alert forensi con contesto; ForensicAnalyzer usa RAG per diagnosi.
- 7) Alerting: CriticalAlert verifica la connettivita (Postgres), deduplica, invia email e marca gli alert in `monitoring_alerts`.
- 8) AI Chat e workflow: endpoint `/api/chat` integra Ollama e puo eseguire azioni (query, email, connessioni); LangGraph orchestra flussi di diagnosi e remediation.
- 9) Dashboard: la UI React mostra inventario, metriche, alert, mailbox, agent control e consente pause/resume del sistema.

## Attori e Ruoli
- DBA/Operations: usa la dashboard per monitorare asset, alert, metriche e lanciare azioni.
- API Gateway (FastAPI): espone endpoint REST e orchestra le chiamate agli agenti e ai servizi AI.
- Scout e Discovery Agent: discovery di database in Docker e su host remoti.
- Collector: raccolta metriche e aggiornamento CMDB.
- Watcher e ForensicAnalyzer: monitoraggio log e analisi RAG.
- CriticalAlert: controllo availability e invio email.
- DailyAudit: report di compliance e obsolescenza.
- AIAssistant/LLM: chat AI e tool calling con contestualizzazione.
- MongoDB: datastore principale (inventory, alert, config).
- Qdrant: knowledge base vettoriale per RAG.
- Ollama: LLM locale per generazione risposte.
- Redis/Celery: code di task e scheduling.
- Frontend React: dashboard operativa per utenti.

## Stack Tecnologico Rilevato
- Linguaggi: Python, TypeScript/JavaScript, Bash/PowerShell, SQL.
- Backend: FastAPI, Motor, Celery, Redis, Requests, Pydantic.
- AI: Ollama, LangChain, LangGraph, Qdrant.
- Data: MongoDB (schema JSON in `mongo/schemas`).
- Frontend: React, Vite, TanStack Query, Lucide Icons.
- Infra/Tools: Docker, Paramiko (SSH), psycopg2, oracledb.
