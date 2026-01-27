# 🚀 Nexi DBA AI: Production Migration Guide

This document outlines the steps required to migrate the **Nexi DBA AI** system from the Lab (Docker) environment to a Production environment (Kubernetes, Hybrid, or Bare Metal).

## 1. Environment Variables
The system is fully configurable via environment variables. Ensure these are set in your production `deployment.yaml` or `.env` file.

### Core Infrastructure
| Variable | Default (Lab) | Production Recommendation |
|:---|:---|:---|
| `MONGODB_HOST` | `localhost` | `mongo-cluster.nexi.internal` |
| `MONGODB_PORT` | `27017` | `27017` (Ensure SSL is enabled) |
| `MONGODB_DB` | `nexi_cmdb_v2` | `nexi_dba_ai_prod` |
| `MONGO_USERNAME` | `admin` | **Use Vault/Secret** |
| `MONGO_PASSWORD` | `nexi2024` | **Use Vault/Secret** |
| `REDIS_HOST` | `localhost` | `redis-cluster.nexi.internal` |

### AI & LLM Services
| Variable | Default (Lab) | Production Recommendation |
|:---|:---|:---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Internal GPU Cluster VIP |
| `QDRANT_HOST` | `http://localhost:7333` | Dedicated Vector DB Cluster |
| `MODEL_NAME` | `deepseek-r1:8b` | `deepseek-r1:70b` (if GPU allows) |

### Security
| Variable | Description |
|:---|:---|
| `JWT_SECRET_KEY` | **MUST CHANGE** in production. |
| `NEXI_MASTER_KEY` | Master key for credential encryption (See `credential_vault.py`). |
| `NEXI_ENCRYPTION_SALT` | Salt for encryption. |

## 2. Agent Deployment Strategy
In production, do **not** run all agents in a single container. Decompose them:

1.  **Orchestrator Pod**: Runs `api_gateway`, `frontend`.
2.  **Sentinel Pod**: Runs `sentinel_workflow.py` (CronJob or Daemon).
3.  **Discovery Pod**: Runs `discovery_agent.py` (CronJob, e.g., nightly).
4.  **Collector Pods**: One per datacenter/subnet (for latency).

## 3. Script Migration
Operational scripts are stored in MongoDB (`system_scripts` collection).
To seed production:
1.  Run `python ops/scripts/migrate_scripts_to_mongo.py` pointing to the PROD MongoDB.
2.  Or use `mongodump` / `mongorestore` to migrate the collection.

## 4. Connectivity Verification
Before enabling the **Auto-Fix** feature in production:
1.  Ensure the **Sentinel Agent** has network access to target databases (Port 1521, 5432, etc.).
2.  Verify `ssh` keys are rotated and injected into the Agent container securely.
3.  **Run `tests/verify_ralph_loop.py`** in a staging environment first.

## 5. Security Checklist
- [ ] **HTTPS**: Configure Nginx/Ingress with valid certificates.
- [ ] **Network Policy**: Restrict access to `api_gateway` (Port 8000) to internal management IPs only.
- [ ] **Role-Based Access**: Create `viewer` and `admin` roles in the Dashboard (Upcoming Feature).
- [ ] **Audit Logging**: Enable generic audit logs in `sentinel_workflow.py` (logs to file/stdout, ensure shipping to Splunk/ELK).

## 6. Auto-Fix Safety Wheels
The RALPH Loop is powerful. For the first week of production:
1.  Set `verifier_agent.py` -> `auto_fixable` default to `False`.
2.  Monitor "Recommended Actions" in the Dashboard.
3.  Enable automation only after validating 50+ correct decisions.

---
*Nexi DBA AI Team - 2026*
