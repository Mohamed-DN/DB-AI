# Documento 2: Roadmap di Miglioramento e Audit Tecnico

## Database e Modello Dati (MongoDB)
**Analisi Stato Attuale:** L'API usa `MongoService` (Motor) mentre molti agenti usano `MongoProxy` basato su `docker exec` (mongosh). La struttura di riferimento e descritta in `mongo/schemas/definitions/...`, ma nel codice coesistono campi duplicati (`identity`, `database_core`, `cluster_identity`).
**Problemi Identificati:**
- Mismatch tra DB name e container: `MongoService` default `m-dn_cmdb_v2`/`m-dn-mongodb` vs `MongoProxy` default `m-dn_cmdb`.
- `MongoProxy` esegue JS via string interpolation con `eval` (fragile, lento, rischio injection).
- Drift di schema e normalizzazione ad-hoc in `api_agents/api_gateway/routers/inventory.py`.
- Dipendenze a path non esistenti (`MongoDB/src` in `api_agents/workers/Collector/src/cmdb_updater.py` e `Tests/validate_system.py`).
- Indici e validation non automatici, assenza di versioning documento.
**Strategia di Miglioramento:** Unificare accesso Mongo su Motor/PyMongo, definire schema canonico e migrazione, introdurre validation e indici, standardizzare naming e connessioni.
**CHECKLIST DI SVILUPPO:**
- [ ] **[Priorita Alta]**: Allineare `MONGODB_DB` e `MONGO_CONTAINER` tra `MongoService` e `MongoProxy`, verificando v2/v3 su `.env.v2`.
- [ ] **[Priorita Alta]**: Sostituire `MongoProxy` negli agenti con un client PyMongo/Motor condiviso.
- [ ] **[Priorita Media]**: Introdurre schema canonico per `inventory_databases` e `monitoring_alerts` con validazione JSON/Pydantic.
- [ ] **[Priorita Media]**: Creare script di indici (unique su `identity.db_unique_name`, TTL su alert opzionali).
- [ ] **[Priorita Media]**: Correggere i path `MongoDB/src` in `cmdb_updater.py` e `Tests/validate_system.py`.

## Backend API Gateway (FastAPI)
**Analisi Stato Attuale:** `api_agents/api_gateway/main.py` espone router modulari per inventory, alert, LLM, metrics, system control e gestione agenti. Le chiamate a Docker e LLM sono eseguite sincrone dentro endpoint async.
**Problemi Identificati:**
- `subprocess.run` e `requests` dentro endpoint async (`routers/system.py`, `routers/llm.py`, `routers/agents.py`) bloccano l'event loop.
- Stato agenti in memoria (`AGENTS_STATE`) non persistente e non condiviso tra processi.
- Nessuna autenticazione/autorizzazione per operazioni critiche (stop container, start agenti, delete email).
- `connection.py` usa `shell=True` e comandi OS-specific (PowerShell), con rischi di abuso.
- `llm.py` esegue azioni da output LLM con validazioni parziali (SQL whitelist fragile).
**Strategia di Miglioramento:** Spostare operazioni lunghe su Celery o threadpool, introdurre auth e RBAC, persistire lo stato agenti, ridurre superfici di esecuzione comandi, rafforzare policy di tool execution.
**CHECKLIST DI SVILUPPO:**
- [ ] **[Priorita Alta]**: Spostare start/stop container e agenti in job Celery o background task non bloccanti.
- [ ] **[Priorita Alta]**: Introdurre autenticazione (JWT/API key) e ruoli per endpoint critici.
- [ ] **[Priorita Media]**: Persistire stato agenti su Mongo/Redis e leggere stato reale dei processi.
- [ ] **[Priorita Media]**: Sostituire `shell=True` con exec sicuro e whitelist container.
- [ ] **[Priorita Media]**: Aggiungere policy di approvazione per azioni LLM (manual approve per query o comandi).

## Agents Runtime (Scout, Discovery, Collector, Watcher, CriticalAlert, Enricher, UserProvisioner, DailyAudit)
**Analisi Stato Attuale:** Gli agenti implementano discovery, metriche, alerting, enrichment e provisioning. Molti componenti usano credenziali di default e `MongoProxy`.
**Problemi Identificati:**
- Metodi mancanti richiamati da Celery (`CollectorAgent.collect_for_database`, `ScoutAgent.scan_all` in `orchestrator/tasks/database_tasks.py`).
- Bug di upsert in Scout con doppio `$set` (`api_agents/workers/Scout/scout_agent.py`).
- `EnricherAgent.enrich_postgres` e incompleto (`api_agents/workers/Enricher/enricher_agent.py`).
- Watcher hard-coded su un singolo container e log path non dinamico.
- Credenziali hard-coded e ruoli troppo privilegiati (UserProvisioner crea SUPERUSER/DBA con password default).
**Strategia di Miglioramento:** Definire un contratto comune per agenti, completare le implementazioni mancanti, rendere discovery/log dinamici, adottare segreti sicuri e ruoli least-privilege, standardizzare output metriche.
**CHECKLIST DI SVILUPPO:**
- [ ] **[Priorita Alta]**: Implementare `collect_for_database` e `scan_all` o aggiornare i task Celery.
- [ ] **[Priorita Alta]**: Correggere l'upsert in Scout (un solo `$set` con documento completo).
- [ ] **[Priorita Media]**: Implementare `enrich_postgres` e normalizzare campi in `state.metrics`.
- [ ] **[Priorita Media]**: Sostituire hard-code in Watcher con discovery da inventory e log strategy configurabile.
- [ ] **[Priorita Alta]**: Spostare credenziali in secret store e ridurre i grant (no SUPERUSER/DBA di default).

## Orchestrator e AI (LLM, RAG, LangGraph, AIAssistant)
**Analisi Stato Attuale:** Esistono un RAG pipeline custom (`orchestrator/rag`), un workflow LangGraph (`api_agents/workers/AIAssistant/langgraph_orchestrator.py`) e un endpoint chat diretto su Ollama (`routers/llm.py`).
**Problemi Identificati:**
- Import path non validi in `orchestrator/core/main.py` e `orchestrator/rag/rag_pipeline.py` (referenze `Orchestrator.*`).
- `api_agents/workers/AIAssistant/main.py` e incompleto (variabili non definite).
- RAG pipeline usa embedding hash (non semantico) e non allineato con `RAGService`.
- Drift config su porte e variabili (`OLLAMA_HOST` vs `OLLAMA_BASE_URL`, `QDRANT_PORT` 6333/7333).
- Workflow results in memoria (`routers/workflows.py`), persi al restart.
**Strategia di Miglioramento:** Consolidare LLM/RAG in un modulo unico, sistemare import, usare embedding reali, centralizzare config, persistere workflow state, introdurre guardrail e timeouts per chiamate LLM.
**CHECKLIST DI SVILUPPO:**
- [ ] **[Priorita Alta]**: Correggere import e path in `orchestrator/core/main.py` e `orchestrator/rag/rag_pipeline.py`.
- [ ] **[Priorita Alta]**: Ripristinare `AIAssistant/main.py` con definizioni mancanti e test di avvio.
- [ ] **[Priorita Media]**: Unificare RAG su `RAGService` con embedding reali (Ollama o sentence-transformers).
- [ ] **[Priorita Media]**: Centralizzare config LLM/Qdrant con un solo schema env.
- [ ] **[Priorita Media]**: Salvare stato workflow su Mongo/Redis e aggiungere endpoint di resume/cancel.

## Frontend Dashboard (React)
**Analisi Stato Attuale:** Dashboard Vite/React con moduli per inventory, alert, chat, metrics, agent control e system pause (`web/dashboard/src`).
**Problemi Identificati:**
- Endpoint non implementati in backend (`/api/action/refresh` usato da `api.ts`).
- Error handling limitato e assenza di fallback per errori di rete o timeout.
- Nessuna autenticazione lato UI.
- Mancanza di paginazione/virtualizzazione su inventory e alert.
**Strategia di Miglioramento:** Allineare il contratto API, aggiungere gestione errori e loading states, introdurre auth, ottimizzare rendering per dataset grandi.
**CHECKLIST DI SVILUPPO:**
- [ ] **[Priorita Media]**: Rimuovere o implementare `/api/action/refresh` con specifica chiara.
- [ ] **[Priorita Media]**: Aggiungere gestione errori e retry user-friendly nelle call API.
- [ ] **[Priorita Alta]**: Integrare auth (token) e proteggere pagine sensibili.
- [ ] **[Priorita Media]**: Implementare paginazione e filtro per inventory/alert.

## Security e Access Control
**Analisi Stato Attuale:** Il sistema espone endpoint operativi e usa credenziali di default in vari agenti e tool.
**Problemi Identificati:**
- Nessuna autenticazione su API, possibile abuso di start/stop container.
- Credenziali hard-coded (`root`, `pippopippo_1234`) e account con privilegi eccessivi.
- Esecuzione comandi da LLM senza approval esplicita.
**Strategia di Miglioramento:** Introdurre auth/RBAC, secret management, policy di approvazione per azioni, audit trail e rotazione credenziali.
**CHECKLIST DI SVILUPPO:**
- [ ] **[Priorita Alta]**: Implementare auth e RBAC per endpoint critici.
- [ ] **[Priorita Alta]**: Spostare tutte le password su secret store e rimuovere default dal codice.
- [ ] **[Priorita Media]**: Ridurre privilegi degli account AIAUTO (least privilege).
- [ ] **[Priorita Media]**: Aggiungere audit log per azioni eseguite da API/LLM.

## Observability e Logging
**Analisi Stato Attuale:** Log via `print` in agenti e backend; Langfuse opzionale in `api_gateway/config.py`.
**Problemi Identificati:**
- Log non strutturati e non correlati tra componenti.
- Nessuna metrica applicativa per agenti e API.
- Log dispersi in file locali senza retention policy.
**Strategia di Miglioramento:** Standardizzare logging JSON, introdurre tracing e metriche, centralizzare i log, aggiungere dashboard Grafana/Prometheus.
**CHECKLIST DI SVILUPPO:**
- [ ] **[Priorita Media]**: Introdurre logging strutturato con correlation-id per API e agenti.
- [ ] **[Priorita Media]**: Esportare metriche (Prometheus) per agenti e API.
- [ ] **[Priorita Media]**: Integrare tracing (Langfuse o OpenTelemetry) e dashboard di osservabilita.

## DevOps e Deployment
**Analisi Stato Attuale:** Script operativi in `ops/scripts`, docker-lab e configurazioni con `.env.v2`. Alcuni comandi sono Windows-specific.
**Problemi Identificati:**
- Drift su porte e variabili (11434/12434, 6333/7333).
- Dipendenze sparse in piu requirements e assenza di lockfile Python.
- Script non portabili tra OS e assenza di validazione config.
**Strategia di Miglioramento:** Consolidare config, introdurre `.env` schema, uniformare porta e container naming, aggiungere setup cross-platform e lockfile.
**CHECKLIST DI SVILUPPO:**
- [ ] **[Priorita Media]**: Creare un unico schema env (documentato) e validarlo all'avvio.
- [ ] **[Priorita Media]**: Consolidare requirements e introdurre lockfile (pip-tools/poetry).
- [ ] **[Priorita Media]**: Aggiornare script per cross-platform o separare chiaramente Windows/Linux.

## Testing e QA
**Analisi Stato Attuale:** Test di sistema in `Tests/validate_system.py` e script di integrazione in `Tests/Integration`.
**Problemi Identificati:**
- Test usano path non esistenti (`MongoDB/src`), quindi falliscono a runtime.
- Nessuna suite di unit test per agenti, API e tool AI.
- Assenza di CI per esecuzione automatica.
**Strategia di Miglioramento:** Ripristinare test di base, aggiungere unit e integration test con docker-compose, automatizzare in CI.
**CHECKLIST DI SVILUPPO:**
- [ ] **[Priorita Alta]**: Sistemare `Tests/validate_system.py` e rimuovere dipendenze a path obsoleti.
- [ ] **[Priorita Media]**: Aggiungere unit test per servizi core (MongoService, routers, tool AI).
- [ ] **[Priorita Media]**: Integrare test di integrazione con Docker in pipeline CI.
