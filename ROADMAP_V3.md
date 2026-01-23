# ROADMAP V3 - Nexi DBA AI

> **Generated**: 2026-01-21
> **Branch**: v3 (development)
> **Status**: Post-Audit Prioritization

---

## 🔴 HIGH Priority (Critical)

### 1. 3-Layer Architecture Compliance
**Issue**: 22 Python scripts at repository root violate Directive/Orchestration/Execution separation

| Task | Files | Effort |
|------|-------|--------|
| Move utility scripts to `execution/` | 15 files | 1h |
| Move test files to `Tests/` | 3 files | 15m |
| Move debug files to `execution/debug/` | 6 files | 15m |
| Update imports in dependent code | All | 30m |

### 2. Missing Directives for New Features
**Issue**: Sprint 1-5 features lack corresponding SOPs

| Directive | Feature | Script |
|-----------|---------|--------|
| `authentication.md` | JWT/RBAC | `auth_service.py` |
| `credential_security.md` | AES-256-GCM | `credential_vault.py` |
| `checkmk_collector.md` | Gateway polling | `collector_agent.py` |
| `metrics_storage.md` | VictoriaMetrics | docker-compose |

### 3. Security: Backend Auth Startup Fix
**Issue**: `ensure_admin_exists()` causes async context error on FastAPI startup

**Fix**: Move admin creation to proper async lifespan handler

---

## 🟡 MEDIUM Priority (Refactoring)

### 4. Code Cleanup
| Task | Files | Effort |
|------|-------|--------|
| Remove log/temp files from root | 8 files | 10m |
| Add files to `.gitignore` | `.gitignore` | 5m |
| Consolidate `.env` files | 3 files | 15m |

### 5. Naming Convention Fixes
| Current | Should Be |
|---------|-----------|
| `CheckMK_Collector/` | `checkmk_collector/` |
| `CriticalAlert/` | `critical_alert/` |
| `DailyAudit/` | `daily_audit/` |

### 6. Documentation Updates
| File | Issue |
|------|-------|
| `docs/architecture/roadmap.md` | Outdated (2024 dates) |
| `README.md` | Missing 3-Layer explanation |
| `execution/README.md` | Incomplete script list |

---

## 🟢 LOW Priority (Enhancements)

### 7. Binary File Organization
- Move `agent.deb`, `agent.rpm` to `ops/packages/`

### 8. Future Features (Backlog)
| Feature | Priority |
|---------|----------|
| Multi-tenant support | Future |
| SSO integration | Future |
| High availability | Future |
| Performance optimization | Future |

---

## 📊 Effort Summary

| Priority | Tasks | Estimated Time |
|----------|-------|----------------|
| 🔴 HIGH | 3 | 2-3 hours |
| 🟡 MEDIUM | 3 | 1 hour |
| 🟢 LOW | 2 | 30 min |
| **TOTAL** | **8** | **4-5 hours** |

---

## ✅ Recently Completed (Sprint 1-5)

- [x] JWT Authentication with RBAC
- [x] VictoriaMetrics Integration
- [x] MongoDB Schema with Indexes
- [x] AES-256-GCM Credential Encryption
- [x] CheckMK Gateway Collector Agent
- [x] Grafana Dashboard Integration
- [x] Graphite Protocol for CheckMK Raw

---

## 🔗 Related Documents

- [Implementation Plan](../implementation_plan.md)
- [System Architecture](docs/architecture/system_architecture.md)
- [Audit Report](docs/audit/DEEP_DIVE_AUDIT.md)
