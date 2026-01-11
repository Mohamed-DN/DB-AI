# ROADMAP_V3

## Priorita Alta
- [ ] Remove hard-coded credentials and secrets from agents and backend
- [ ] Replace hard-coded absolute paths with env or config
- [ ] Modularize WebInterface/backend/main.py and separate routers
- [ ] Add auth and access control for /api/raw, /api/agents, /api/chat
- [ ] Standardize system_config keys and ensure agents honor global_status
- [ ] Fix remaining encoding artifacts and inconsistent logging

## Priorita Media
- [ ] Introduce pydantic response models and shared API types
- [ ] Add integration tests for auto-discovery, agent triggers, pause/resume, and chat
- [ ] Consolidate env vars (MONGO_ vs MONGODB_) and document in one place
- [ ] Replace docker exec MongoProxy with direct PyMongo fallback and retries
- [ ] Implement a background scheduler for periodic jobs

## Priorita Bassa
- [ ] UI polish: filters, bulk actions, export
- [ ] Automate RAG ingestion and knowledge refresh
- [ ] Add reporting dashboards for compliance and capacity
