# 🛠️ Scripts

> Automation scripts for deploying, managing, and maintaining the Nexi DBA AI environment.

This directory contains Powershell and Shell scripts to handle the lifecycle of the application, including starting containers, cleaning up resources, and managing models.

---

## 🚀 Core Lifecycle (V2)

These are the primary scripts you should use.

| File | OS | Description |
|------|----|-------------|
| **`setup_v2.ps1`** | **Windows** | **Start Here**. Deploys the entire stack (Docker, Backend, Frontend, Ollama) and ensures all components are connected. |
| **`setup_v2.sh`** | **Linux/Mac** | Linux equivalent of the setup script. |
| **`cleanup_v2.ps1`** | **Windows** | Tears down the environment, stops containers, and cleans up Docker networks. |

---

## 🔧 Utilities & Tools

| File | Description |
|------|-------------|
| **`pull_models.ps1`** | Downloads the required LLM models (e.g., qwen2.5:7b) into Ollama. |
| **`restart_ollama_gpu.ps1`** | Force restarts the Ollama service, specifically useful if GPU offloading hangs. |
| **`migrate_storage_to_collection.py`** | Python script to migrate storage-related metadata between DB structures. |
| **`seed_*.py`** | Various scripts (`seed_oracle_demo.py`, `seed_postgres_deep.py`) to populates the database with dummy data for testing agents. |

---

## ⚠️ Legacy / Deprecated

These scripts may still work but `setup_v2` is the recommended method.

- `start-all.ps1` / `stop-all.ps1`: Older start scripts.
- `start-everything.ps1` / `stop-everything.ps1`: Another variant of start scripts.
- `start_monitoring.ps1`: Specific sub-module start.

---

## 💡 Usage Example

To start the full environment on Windows:

```powershell
.\scripts\setup_v2.ps1
```

To just restart Ollama models:

```powershell
.\scripts\pull_models.ps1
```
