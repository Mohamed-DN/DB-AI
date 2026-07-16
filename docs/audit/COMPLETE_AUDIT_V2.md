# M-DN DBA AI - Complete Technical Audit v2

**Data Audit**: 2026-01-26
**Scope**: Full codebase analysis across all domains
**Output**: Granular improvement plan with 50+ specific tasks

---

## 📊 Executive Summary

| Domain | Status | Critical Issues | Tasks |
|--------|--------|-----------------|-------|
| API Gateway | 🟢 Good | 2 | 8 |
| Agent Workers | 🟡 Medium | 3 | 12 |
| Frontend | 🟢 Good | 1 | 7 |
| LLM/RAG | 🟢 Good | 1 | 6 |
| Database Layer | 🟡 Medium | 2 | 8 |
| Security | 🟡 Medium | 3 | 9 |
| DevOps | 🔴 Critical | 2 | 6 |
| Testing | 🔴 Critical | 2 | 5 |

**Total Tasks**: 61

---

## 🔴 PRIORITY 0: Critical Fixes (Immediate)

### P0.1 Scout Agent - Double `$set` Bug
**File**: `api_agents/workers/Scout/scout_agent.py`
**Line**: 212
**Issue**: MongoDB syntax error in upsert - two `$set` operators
```python
# BROKEN:
{{ $set: {db_json}, $set: {{ "state.status": "UP" }} }}
```
**Fix**: Merge into single `$set`
**Effort**: 30 min

---

### P0.2 Hardcoded Default Admin Password
**File**: `api_agents/api_gateway/services/auth_service.py`
**Line**: 213
**Issue**: Default password `M-DNAdmin2024!` printed to console
**Fix**: Require password via env var or setup wizard
**Effort**: 1 hour

---

### P0.3 MongoProxy Still Used in Agents
**Files**:
- `api_agents/workers/Scout/scout_agent.py`
- `api_agents/workers/Collector/collector_agent.py`
- `api_agents/workers/Watcher/watcher_agent.py`
- `api_agents/workers/CriticalAlert/critical_alert_agent.py`
- `orchestrator/core/mongo_proxy.py`
**Issue**: Subprocess-based MongoDB access (slow, risky)
**Fix**: Migrate to PyMongo sync client
**Effort**: 4 hours

---

## 🟡 PRIORITY 1: High Impact Improvements

### 1.1 API Gateway Domain (8 tasks)

| ID | Task | File | Effort |
|----|------|------|--------|
| API-1 | Replace sync `subprocess.run` with `asyncio.create_subprocess_exec` | `routers/system.py` L224 | 1h |
| API-2 | Replace sync `requests` with `httpx.AsyncClient` | `routers/llm.py` L291 | 2h |
| API-3 | Remove hardcoded artifact paths | `routers/system.py` L17-20 | 30m |
| API-4 | Persist agent state to Redis instead of in-memory | `config.py` `AGENTS_STATE` | 2h |
| API-5 | Add rate limiting to `/chat` endpoint | `routers/llm.py` | 1h |
| API-6 | Improve SQL whitelist validation | `routers/llm.py` L365-380 | 2h |
| API-7 | Add request validation with Pydantic models | All routers | 3h |
| API-8 | Implement proper error responses (RFC 7807) | All routers | 2h |

---

### 1.2 Agent Workers Domain (12 tasks)

| ID | Task | File | Effort |
|----|------|------|--------|
| AGT-1 | Fix Scout double `$set` bug | `Scout/scout_agent.py` L212 | 30m |
| AGT-2 | Create `SyncMongoService` with PyMongo | New file | 2h |
| AGT-3 | Migrate Scout to `SyncMongoService` | `Scout/scout_agent.py` | 1h |
| AGT-4 | Migrate Collector to `SyncMongoService` | `Collector/collector_agent.py` | 1h |
| AGT-5 | Migrate Watcher to `SyncMongoService` | `Watcher/watcher_agent.py` | 1h |
| AGT-6 | Migrate CriticalAlert to `SyncMongoService` | `CriticalAlert/critical_alert_agent.py` | 1h |
| AGT-7 | Remove hardcoded credentials from UserProvisioner | `Scout/user_provisioner.py` | 1h |
| AGT-8 | Add structured logging (JSON format) | All agents | 2h |
| AGT-9 | Implement health check endpoint for agents | All agents | 1h |
| AGT-10 | Add graceful shutdown handling | All agents | 1h |
| AGT-11 | Implement Celery task wrappers for agents | New files | 3h |
| AGT-12 | Add agent metrics (Prometheus exporter) | New file | 2h |

---

### 1.3 Frontend Domain (7 tasks)

| ID | Task | File | Effort |
|----|------|------|--------|
| FE-1 | Add loading spinners to all data fetches | Multiple components | 2h |
| FE-2 | Implement proper error boundaries | `App.tsx` | 1h |
| FE-3 | Add toast notifications for actions | New component | 1h |
| FE-4 | Implement pagination for Inventory table | `InventoryTable.tsx` | 2h |
| FE-5 | Implement pagination for Alerts table | `AlertsPanel.tsx` | 2h |
| FE-6 | Add dark mode toggle persistence | `App.tsx` | 30m |
| FE-7 | Remove mock data fallbacks (use error states) | `api.ts` L150-160 | 1h |

---

### 1.4 LLM/RAG Domain (6 tasks)

| ID | Task | File | Effort |
|----|------|------|--------|
| LLM-1 | Add streaming support for chat endpoint | `routers/llm.py` | 3h |
| LLM-2 | Implement context window truncation | `routers/llm.py` L209-214 | 1h |
| LLM-3 | Add RAG source citations in responses | `AIAssistant/services/rag_service.py` | 2h |
| LLM-4 | Implement hybrid search (keyword + semantic) | `AIAssistant/services/rag_service.py` | 3h |
| LLM-5 | Add model warmup on startup | `AIAssistant/main.py` | 1h |
| LLM-6 | Implement prompt versioning/templates | New file | 2h |

---

### 1.5 Database Layer Domain (8 tasks)

| ID | Task | File | Effort |
|----|------|------|--------|
| DB-1 | Create MongoDB indexes for inventory_databases | `mongo/scripts/create_indexes.js` | 1h |
| DB-2 | Create MongoDB indexes for monitoring_alerts | Same | 30m |
| DB-3 | Implement TTL index for old alerts | Same | 30m |
| DB-4 | Add unique index on `identity.db_unique_name` | Same | 30m |
| DB-5 | Create Pydantic schema for inventory document | New file | 2h |
| DB-6 | Add JSON Schema validation to MongoDB | `mongo/schemas/` | 2h |
| DB-7 | Consolidate `.env` files (remove `.env.v2`) | Config | 1h |
| DB-8 | Add database connection pooling limits | `mongo_service.py` | 1h |

---

### 1.6 Security Domain (9 tasks)

| ID | Task | File | Effort |
|----|------|------|--------|
| SEC-1 | Change default JWT secret to require env var | `auth_service.py` L18 | 30m |
| SEC-2 | Require admin password via setup wizard | `auth_service.py` L213 | 2h |
| SEC-3 | Add RBAC enforcement to all sensitive endpoints | `routers/*.py` | 4h |
| SEC-4 | Implement API rate limiting (per-user) | `main.py` | 2h |
| SEC-5 | Add audit logging for destructive actions | New middleware | 2h |
| SEC-6 | Remove all hardcoded passwords from code | Multiple files | 2h |
| SEC-7 | Implement credential vault integration | `services/credential_vault.py` | 3h |
| SEC-8 | Add CORS origin validation (remove `*`) | `config.py` | 30m |
| SEC-9 | Implement API key authentication (for services) | New file | 2h |

---

### 1.7 DevOps Domain (6 tasks)

| ID | Task | File | Effort |
|----|------|------|--------|
| OPS-1 | Port `setup_v2.ps1` to Bash | `ops/scripts/setup_v2.sh` | 2h |
| OPS-2 | Port `cleanup_v2.ps1` to Bash | New file | 1h |
| OPS-3 | Port `start-everything.ps1` to Bash | New file | 1h |
| OPS-4 | Create unified `.env.schema` with validation | New file | 2h |
| OPS-5 | Add requirements.lock (pip-tools) | New file | 1h |
| OPS-6 | Create Docker healthchecks for all services | `docker-compose.yml` | 1h |

---

### 1.8 Testing Domain (5 tasks)

| ID | Task | File | Effort |
|----|------|------|--------|
| TEST-1 | Fix `Tests/validate_system.py` import paths | `Tests/validate_system.py` | 1h |
| TEST-2 | Add pytest fixtures for MongoDB | `tests/conftest.py` | 2h |
| TEST-3 | Add unit tests for MongoService | `tests/test_mongo_service.py` | 3h |
| TEST-4 | Add unit tests for AuthService | `tests/test_auth_service.py` | 3h |
| TEST-5 | Add integration tests for API endpoints | `tests/test_api_*.py` | 4h |

---

## 📋 Implementation Roadmap

### Phase 1: Critical Fixes (Week 1)
- [ ] P0.1 - Fix Scout `$set` bug
- [ ] P0.2 - Secure default admin password
- [ ] P0.3 - Create SyncMongoService (AGT-2)
- [ ] AGT-3 to AGT-6 - Migrate agents away from MongoProxy
- [ ] SEC-1, SEC-6 - Remove hardcoded secrets

### Phase 2: API & Performance (Week 2)
- [ ] API-1, API-2 - Async subprocess and httpx
- [ ] API-4 - Redis-based agent state
- [ ] DB-1 to DB-4 - MongoDB indexes
- [ ] LLM-1 - Streaming chat

### Phase 3: DevOps & Security (Week 3)
- [ ] OPS-1 to OPS-3 - Bash scripts for Linux
- [ ] SEC-3, SEC-4 - RBAC and rate limiting
- [ ] SEC-5 - Audit logging
- [ ] OPS-4 - Unified env schema

### Phase 4: Testing & Polish (Week 4)
- [ ] TEST-1 to TEST-5 - Test suite
- [ ] FE-1 to FE-7 - Frontend improvements
- [ ] AGT-8, AGT-12 - Observability

---

## 📂 Files to Create

1. `api_agents/shared/sync_mongo_service.py` - PyMongo sync client for agents
2. `api_agents/api_gateway/middleware/rate_limit.py` - Rate limiting
3. `api_agents/api_gateway/middleware/audit_log.py` - Audit logging
4. `mongo/scripts/create_indexes.js` - MongoDB indexes
5. `ops/scripts/setup_v2.sh` - Linux setup script
6. `ops/scripts/cleanup_v2.sh` - Linux cleanup script
7. `.env.schema` - Environment variable documentation
8. `tests/conftest.py` - Pytest fixtures
9. `tests/test_mongo_service.py` - MongoService tests
10. `tests/test_auth_service.py` - AuthService tests

---

## 📂 Files to Delete (Technical Debt)

1. `api_agents/api_gateway/main_backup.py` - 68KB legacy file
2. `orchestrator/core/mongo_proxy.py` - After migration complete
3. Multiple debug scripts in root (clean after use)
