# 🧠 NExi AI CMDB - AI Context & Guidelines

> **IMPORTANT**: This file acts as the primary source of truth for any AI working on this project. READ THIS FIRST.

## 1. Project Architecture (V2 Shadow Mode)
The project runs a **V2 Shadow Environment** parallel to the legacy V1, completely isolated by ports.

- **Infrastructure**: Docker Compose (`docker-lab/docker-compose-v2.yml`).
- **Configuration**: ALL configuration (ports, passwords, hosts) MUST be read from `.env.v2`.
- **Port Strategy**: V2 ports are V1 ports + 1000.
    - Frontend: `4002` (V1: 3002)
    - Backend: `9000` (V1: 8000)
    - MongoDB: `28017`
    - Qdrant: `7333`
    - Ollama: `12434`

## 2. automation & Portability (Critical)
**Rule #1**: The system MUST be portable and start with a SINGLE command.
- **Startup Script**: `.\scripts\setup_v2.ps1`
    - This script handles: Docker start, Backend start (pip modules), Frontend start (npm modules).
    - NEVER ask the user to manually install dependencies or run multiple commands.
- **Portability**: Do NOT hardcood paths (e.g., `C:\AI-Nexi`). Use relative paths or script root resolution (`$PSScriptRoot`).

## 3. Backend (FastAPI)
- **Entry Point**: `WebInterface/backend/main.py`
- **Agent Management**: Agents are started/stopped via `subprocess` calls in the backend.
- **Connections**:
    - NEVER hardcode URLs like `localhost:6333`.
    - ALWAYS use `os.getenv("QDRANT_HOST")` or similar from `.env.v2`.
- **RAG Status**: The endpoint `/api/rag/status` must checks the configured V2 ports.

## 4. Frontend (React + Vite)
- **UI Design**:
    - **Aesthetic**: Premium, Dark Mode, Glassmorphism, "Uber Eats" style green/gold accents.
    - **Modals**: Use custom `ActionModal` or `ConnectionModal`. NEVER use `alert()`.
- **Configuration**:
    - **Agents Panel**: The ONLY place to configure agent intervals and start/stop.
    - **Settings**: Do not create duplicate settings pages.
- **Tech**: Tailwind CSS, Lucide Icons, React Query.

## 5. Agents & Database
- **AIAUTO User**: The system automatically provisions a DBA user `aiauto` on all discovered databases (Oracle, PG, MySQL).
- **Discovery**: `ScoutAgent` runs periodically.
- **Vector DB**: Qdrant stores RAG embeddings. Must be online (Port 7333).

## 6. Git Workflow
- **Branch `v2`**: Stable Release (Shadow Mode Complete).
- **Branch `v3`**: Experimental / Next Copy.
- **Ignore**: `__pycache__`, `*.pyc`, `node_modules` must stay in `.gitignore`.

## 7. Common Fixes (Memory Bank)
- **Qdrant Offline?** Check if Backend is reading `QDRANT_PORT` env var.
- **React Build Fail?** Check `npm install` and `react-router-dom`.
- **Script Error?** Ensure `setup_v2.ps1` allows `PowerShell -ExecutionPolicy Bypass`.

---
**Verified on**: 2026-01-11
**Version**: V2.0 (Shadow Release)
