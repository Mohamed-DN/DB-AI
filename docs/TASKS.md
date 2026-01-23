# Nexi DBA AI - Enterprise Architecture Upgrade

## Phase 1-2: Foundation ✅ COMPLETE
- [x] CheckMK API client (in Bridge Worker)
- [/] Bi-directional alert sync
- [x] Automated alert validation (Real Agent Integration)
- [x] Deploy CheckMK Agents (Real .deb/.rpm)
- [x] DB Monitoring Users (Created)
- [x] Register Real Hosts in CheckMK
- [x] Disaster Simulation (CPU/IO)
- [x] Frontend: Embed Grafana & CheckMK (Iframe Integration)
- [x] Frontend: Fix Metrics API Connection 
- [x] Frontend: Fix Grafana 404 & CheckMK Iframe Blocking (X-Frame-Options)
- [x] Fix Inventory Duplicates (38+ entries -> Cleaned)
- [x] Frontend: Add Quick Links (Grafana/CheckMK)
- [x] Frontend: Add Dynamic Role Selector (Admin/Dev/Viewer)
- [x] Fix Inventory Duplicates (38+ entries -> Cleaned)
- [x] Frontend: Add Quick Links (Grafana/CheckMK)
- [x] Frontend: Add Dynamic Role Selector (Admin/Dev/Viewer)
- [x] False positive detection & auto-acknowledgement

## Phase 3: Production Infrastructure ✅ COMPLETE
- [x] Celery + Redis distributed task queue
- [/] FastAPI production optimization
- [x] Redis caching layer (Planned)

## Phase 4: Multi-Agent AI (LangGraph) ✅ COMPLETE
- [x] LangGraph workflow (Diagnostic, Remediation, Execution Agents)
- [x] Workflow API Endpoint
- [x] Langfuse Integration & Tracing
- [x] Frontend: "Open Langfuse" Quick Action
- [x] Create Central & Sectional Roadmap

## Phase 5: Deep Monitoring & Simulation (CURRENT)
- [x] **Deploy CheckMK Agents**: Install agents & DB plugins on Oracle/Postgres containers
- [ ] **Real-world Load Testing**: Use `pgbench` and `sysbench` against registered hosts
- [ ] **DB Monitoring Users**: Create `checkmk` users on databases
- [ ] **Grafana Integration**: Connect CheckMK datasource to Grafana
- [ ] **Disaster Simulation**: Scripts for CPU spike, deadlock, and IO saturation
- [ ] **AI Validation Loop**: Verify AI correctly identifies simulated incidents

## Phase 6: Vector & Tool Optimization (CURRENT)
- [x] **Resolve Dependency Hell**: Fix conflicts (Upgraded to 0.3.x + LangGraph)
- [x] **MongoDB Tool Registry**: Create `ai_tools` collection and loader script
- [x] **Migrate Existing Tools**: Move `inventory_tools`, `action_tools` to MongoDB
- [x] **Dynamic Agent Loader**: Update `AIAssistant` to load tools at runtime
- [x] **Qdrant Optimization**: Implement "Domain Chunking" (separate collections/filters)
- [x] **Knowledge Ingestion**: Scripts to ingest SOPs/Runbooks into Qdrant
- [ ] **Vector DB for Historical Alerts**: Store alert history in Qdrant for RAG

## Phase 7: Technical Audit & Refactoring (High Priority)
- [ ] **Database**: Align `MONGODB_DB` & Replace `MongoProxy` with `MongoService` (Motor) in Agents
- [ ] **Scout Agent**: Fix double `$set` Upsert Bug
- [ ] **API Gateway**: Move start/stop actions to Celery (Async)
- [ ] **Security**: Implement RBAC & Secret Management
- [ ] **Frontend**: Add Auth & Error Handling
- [ ] **Testing**: Fix `validate_system.py` paths
- [ ] **Ops**: Port PowerShell scripts to Bash (`.sh`) for Red Hat
- [ ] **Ops**: Validate and fix Docker volume paths for Linux
