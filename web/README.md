# 🌐 Web Frontend

## 🎯 Scopo
Questa cartella contiene tutto il codice relativo all'interfaccia utente (UI) del sistema M-DN DBA AI. Include sia la nuova dashboard React che la legacy UI.

## 📂 File Manifest
- **`dashboard/`**: (Directory) La nuova applicazione React (Vite + TypeScript) che funge da interfaccia principale.
- **`legacy/`**: (Directory) La vecchia interfaccia HTML/JS, mantenuta per compatibilità o fallback.

## 🔗 Connessioni
- **Verso `api_agents/api_gateway`**: La dashboard chiama gli endpoint REST (es. `/api/inventory`) esposti dal backend FastAPI sulla porta **9000**.
- **Verso Utente**: Espone il servizio sulla porta **4002** (Vite dev server) o tramite Nginx in produzione.
