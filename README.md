# Nexi DBA AI (v3)

## Scopo del progetto
Nexi DBA AI is an AI assisted CMDB and database monitoring platform. It discovers databases, stores inventory and metrics, raises alerts, and provides a web dashboard and AI chat.

## Installazione e Setup
Prerequisites: Docker Desktop, Python 3.10+, Node.js 18+, Git.

1) Clone the repository
   git clone https://github.com/ThomasNexi/Nexi_DB_AI.git
   cd Nexi_DB_AI
2) Configure environment in .env (v3) or .env.v2 (shadow mode).
   Key variables: MONGODB_HOST, MONGODB_DB, MONGO_USERNAME, MONGO_PASSWORD, OLLAMA_HOST, QDRANT_HOST, VITE_MONGO_EXPRESS_PORT, ALERT_EMAIL, SMTP_USER, SMTP_PASSWORD.
3) Start lab infrastructure:
   cd docker-lab
   docker-compose up -d
   Or run scripts/setup_v2.ps1 to bootstrap v3 ports.
4) Backend:
   pip install -r WebInterface/backend/requirements.txt
   cd WebInterface/backend
   uvicorn main:app --reload --port 9000
5) Frontend:
   cd WebInterface/frontend-react
   npm install
   npm run dev:v2
6) Optional agents (CLI):
   python Agents/Scout/main.py --once
   python Agents/Collector/main.py --once
   python Agents/CriticalAlert/main.py --once --email you@example.com

## Architettura
- WebInterface/backend: FastAPI API and agent controls.
- WebInterface/frontend-react: React dashboard and panels.
- Agents: Scout, Collector, Watcher, CriticalAlert, CheckMK Bridge, Forensic Analyzer.
- Orchestrator: LLM and RAG pipeline (Ollama + Qdrant).
- MongoDB: CMDB collections and system_config.
- docker-lab: local infra (MongoDB, Redis, Qdrant, Ollama, sample DBs).

Data flow: Agents -> MongoDB, Orchestrator -> LLM/Qdrant, UI -> Backend -> MongoDB/Agents.

## Utilizzo
- Open the dashboard at http://localhost:4002 (v3) or http://localhost:3002 (v1).
- Run Auto-Discovery to populate inventory.
- Use Agents panel to start and stop agents and tune intervals.
- Use Explorer to browse collections and inspect documents.
- Use AI Chat to query inventory and alerts.
- Open Mongo Express at http://localhost:PORT from VITE_MONGO_EXPRESS_PORT.
