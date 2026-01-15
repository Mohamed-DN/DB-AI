# Frontend React

## Scopo del progetto
Single page dashboard for inventory, alerts, agents, and AI chat.

## Installazione e Setup
- npm install
- npm run dev:v2 (v3 ports) or npm run dev (v1 ports)
Set VITE_MONGO_EXPRESS_PORT in the root .env if you want the Mongo button.

## Architettura
- src/App.tsx: layout and tabs
- src/components: UI panels
- src/hooks: React Query hooks
- src/services/api.ts: API layer

## Utilizzo
Start the dev server and use the UI to trigger Auto-Discovery and agent actions.
