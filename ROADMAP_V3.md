# ROADMAP V3

Development roadmap aligned with the **3-Layer Architecture**.

---

## High Priority (Architecture & Security)

### Architecture Violations
- [ ] Split `main.py` (~1066 lines) into modular routers
- [ ] Move DB connection logic to `execution/connect_database.py`
- [ ] Move agent spawn logic to `execution/spawn_agent.py`

### Security
- [ ] Remove hardcoded credentials from agents and backend
- [ ] Add authentication to sensitive endpoints (`/api/raw`, `/api/agents`)
- [ ] Validate all user inputs (injection prevention)

### Configuration
- [ ] Consolidate env vars (`MONGO_` vs `MONGODB_`)
- [ ] Document all env vars in `.env.example` ✅

---

## Medium Priority (Code Quality)

### Backend Refactoring
- [ ] Create `routers/agents.py` for agent management
- [ ] Create `routers/inventory.py` for DB CRUD
- [ ] Create `routers/config.py` for system config
- [ ] Add Pydantic response models
- [ ] Replace MongoProxy `docker exec` with PyMongo fallback

### Execution Layer
- [ ] Create `execution/analyze_alert.py` for AI analysis
- [ ] Add retry logic to all execution scripts
- [ ] Standardize error responses

### Testing
- [ ] Add integration tests for auto-discovery
- [ ] Add tests for agent start/stop
- [ ] Add tests for pause/resume

---

## Low Priority (Polish)

### UI Improvements
- [ ] Add filters and bulk actions to Inventory
- [ ] Add export functionality (CSV, JSON)
- [ ] Improve mobile responsiveness

### AI Features
- [ ] Automate RAG knowledge refresh
- [ ] Add multi-turn conversation context
- [ ] Implement action confirmation modal

### Reporting
- [ ] Add compliance dashboards
- [ ] Add capacity planning reports
- [ ] Add SLA tracking

---

## Completed ✅

- [x] Create `ARCHITECTURE.md`
- [x] Create `.env.example`
- [x] Update `README.md` with 3-Layer reference
- [x] Standardize all directives format
- [x] Fix Mongo Express port (V2)
- [x] Fix `GATEWAY_SUFFIX` for Scout discovery
- [x] Create `cleanup_v2.ps1`
- [x] Zero-config `setup_v2.ps1`
