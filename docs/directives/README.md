# 📜 Directives (SOPs)

> Standard Operating Procedures and Context documents for the AI Agents and Orchestrator.

This directory contains the "Rules of Engagement" and detailed logic explanations that guide the autonomous behavior of the system. These files are often injected into the prompt context of the LLM or used as reference for implementation.

---

## 🤖 AI & Interaction

| File | Description |
|------|-------------|
| **`ai_chat.md`** | Defines the persona, tone, and constraints for the AI Chat interface. |
| **`system_control.md`** | Protocols for pausing, resuming, or shutting down system components. |

---

## 🔍 Discovery & Monitoring

| File | Description |
|------|-------------|
| **`database_discovery.md`** | Logic flow for how new databases are discovered and validated. |
| **`container_monitoring.md`** | Rules for mapping Docker container stats to database health. |
| **`metric_collection.md`** | Definition of key metrics (CPU, IOPS, Wait Events) to be collected. |

---

## 🚨 Alerting & Integration

| File | Description |
|------|-------------|
| **`alert_processing.md`** | Decision tree for classifying and deduplicating alerts. |
| **`email_notifications.md`** | Templates and logic for sending email alerts. |
| **`checkmk_sync.md`** | Protocol for synchronizing inventory with the corporate CheckMK system. |
