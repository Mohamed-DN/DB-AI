# Agents

> Background workers for database discovery, monitoring, auditing, and alerting.

This directory contains the autonomous agents that interact directly with the database infrastructure and other external systems. They act as the "Hands" of the Nexi DBA AI system.

## 📂 Directory Contents

### **Active Agents**

| Directory | Agent Name | Description | Key Command |
|-----------|------------|-------------|-------------|
| **`Scout/`** | **Scout Agent** | discovery of database containers (Docker) and initial inventory registration. | `python Agents/Scout/main.py --once` |
| **`Collector/`** | **Collector Agent** | Polling agent that gathers real-time metrics (CPU, Memory, Connections) from databases. | `python Agents/Collector/main.py` |
| **`CriticalAlert/`** | **Critical Alert** | Monitoring service that checks system health and sends alerts (Email/Webhook) for failures. | `python Agents/CriticalAlert/main.py` |
| **`DailyAudit/`** | **Audit Agent** | Performs daily compliance and configuration checks against registered databases. | `python Agents/DailyAudit/main.py` |
| **`Watcher/`** | **Watcher Agent** | Monitors database logs (alert logs) for specific error patterns. | `python Agents/Watcher/main.py` |
| **`AIAssistant/`** | **AI Assistant** | Helper modules for handling agent-specific AI tasks or queries. | N/A |

### **Integration & Legacy**

| Directory | Name | Description |
|-----------|------|-------------|
| **`CheckMK_Bridge/`** | **CheckMK Bridge** | Connectors for integrating with CheckMK monitoring systems. |
| **`Monitor/`** | **Monitor Lib** | Shared library for monitoring functions used by multiple agents. |

## 📄 Files

| File | Description |
|------|-------------|
| **`main.py`** | General entry point or utility script for triggering agent-related tasks. |
| **`__init__.py`** | Makes this directory a Python package. |

## 🔗 Related Documentation

- **[Detailed Agent Commands](../docs/agent_extraction_commands.md)**: How agents interact with databases.
