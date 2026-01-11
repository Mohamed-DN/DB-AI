# WebInterface

## Scopo del progetto
Provides the REST API and the web dashboard for Nexi DBA AI.

## Installazione e Setup
Backend:
- pip install -r WebInterface/backend/requirements.txt
- cd WebInterface/backend
- uvicorn main:app --reload --port 9000

Frontend:
- cd WebInterface/frontend-react
- npm install
- npm run dev:v2

Vite reads VITE_* variables from the repo root .env.

## Architettura
- backend/main.py: API endpoints, agent triggers, system_config handling.
- frontend-react/src/App.tsx: navigation and layout.
- frontend-react/src/services/api.ts: API client.
- frontend-react/src/components: dashboard panels.

## Utilizzo
Open http://localhost:4002 and use the dashboard to run auto discovery and manage agents.
