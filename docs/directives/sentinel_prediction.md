# 🔮 Sentinel Prediction Directive

> Standard Operating Procedure for predictive alerting and autonomous remediation.

---

## 🎯 AI Context

```yaml
Purpose: Predict database issues before they occur using ML/AI
Agent: Sentinel (Predictor + Verifier + Action)
Location: api_agents/workers/Sentinel/
Trigger: API endpoint POST /api/action/sentinel
Output: Alerts, Emails, Remediation procedures
```

---

## 📋 Procedure

### 1. Data Ingestion
- Query VictoriaMetrics for historical time-series data
- Collect last 24h-7d of metrics per database
- Metrics: CPU, Memory, I/O, Connections, Wait Events

### 2. Prediction (Predictor Agent)
- Run time-series forecasting (ARIMA/Prophet)
- Detect patterns leading to:
  - Out of Memory (OOM)
  - Lock contention
  - Storage exhaustion
  - Connection pool saturation
- Output: Probabilistic alert with confidence score

### 3. Verification (Verifier Agent)
- Cross-check prediction against real-time database status
- Use LLM to classify:
  - **REAL/CRITICAL**: Immediate action required
  - **FALSE_ALARM**: Normal fluctuation, no action
- Consider context from RAG knowledge base

### 4. Action Workflow
| Classification | Action |
|----------------|--------|
| REAL/CRITICAL | Send urgent email with fix procedure |
| FALSE_ALARM | Send status report, log for analysis |

### 5. Remediation Reference
- Query RAG (Qdrant) for relevant SOPs
- Include step-by-step procedure in alert email
- Reference existing scripts in `execution/` directory

---

## ⚙️ Configuration

```yaml
# In system_config collection
sentinel:
  enabled: true
  prediction_horizon_hours: 4
  confidence_threshold: 0.75
  data_lookback_days: 7
  alert_email: dba-team@m-dn.lab
```

---

## 🔗 Related

- [Sentinel Agent](../../api_agents/workers/Sentinel/)
- [Predictor Agent](../../api_agents/workers/Sentinel/predictor_agent.py)
- [Verifier Agent](../../api_agents/workers/Sentinel/verifier_agent.py)
- [Alert Processing Directive](./alert_processing.md)
- [Email Notifications Directive](./email_notifications.md)
