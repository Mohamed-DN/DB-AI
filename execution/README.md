# ⚡ Execution Scripts

> Deterministic Python scripts for direct database interaction and state management.

This directory contains standalone scripts often used by Agents, the Orchestrator, or Administrators to perform specific, atomic actions on the environment.

---

## 🏗️ Setup & Registration

| File | Description |
|------|-------------|
| **`create_aiauto_user.py`** | Creates the `c##aiauto` user on Oracle databases (PDBs) to allow agent access. |
| **`setup_db_access.py`** | Configures permissions and access roles for the AI agents in the target DBs. |
| **`register_database.py`** | Manually registers a database into the MongoDB inventory. |
| **`discover_docker_databases.py`** | Scans local Docker containers to find and register running databases. |
| **`add_oracle_db.py`** | Helper for adding Oracle instances. |

---

## 🧹 Maintenance & Cleanup

| File | Description |
|------|-------------|
| **`cleanup_mongo.py`** | Removes stale or invalid entries from MongoDB. |
| **`cleanup_pdb_entries.py`** | Specifically cleans up Pluggable Database (PDB) metadata. |
| **`force_clear.py`** | **Danger**. Wipes the inventory for a fresh start. |
| **`reset_config.py`** | Resets system configuration (e.g., agent intervals) to defaults. |

---

## 🧪 Verification & Debug

| File | Description |
|------|-------------|
| **`check_status.py`** | Quick health check of the system's components. |
| **`debug_system.py`** | Runs diagnostics to identify issues. |
| **`verify_pdbs.py`** | Verifies that PDBs are reachable and correctly registered. |

---

## 🌱 Seeding

| File | Description |
|------|-------------|
| **`seed_mongodb.py`** | Populates MongoDB with initial seed data or default configuration. |
