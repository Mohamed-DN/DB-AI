# 🤖 Agents - Background Workers

> Questa directory contiene i 6 agenti di background che compongono il sistema di monitoraggio autonomo.

---

## 📋 Overview

| Agent | Intervallo | Scopo |
|-------|------------|-------|
| **Scout** | 60s | Auto-discovery database in Docker |
| **Collector** | 30s | Raccolta metriche performance |
| **Watcher** | 10s | Streaming log containers |
| **CriticalAlert** | 30s | Email per alert critici |
| **CheckMK_Bridge** | 60s | Sync metriche da CheckMK |
| **AIAssistant** | on-demand | RAG-powered assistant |
| **DailyAudit** | 24h | Report giornalieri |
| **Monitor** | 10s | Container health monitoring |

---

## 🔧 Struttura

```
Agents/
├── Scout/
│   └── main.py           # Discovery via docker ps
├── Collector/
│   ├── main.py           # Orchestrator metriche
│   └── src/extractors/   # Extractors per engine (Oracle, Postgres, etc.)
├── Watcher/
│   └── main.py           # Log streaming con pattern matching
├── CriticalAlert/
│   ├── main.py           # Email sender
│   └── critical_alert.py # Core logic
├── CheckMK_Bridge/
│   └── main.py           # API sync con CheckMK
├── AIAssistant/
│   └── main.py           # RAG pipeline interface
├── DailyAudit/
│   └── main.py           # Daily report generator
└── main.py               # Entry point per avvio multiplo
```

---

## 🚀 Avvio

### Singolo Agente
```powershell
cd Agents/Scout
python main.py --once  # Esecuzione singola
python main.py         # Loop continuo
```

### Tutti gli Agenti
```powershell
python Agents/main.py
```

---

## ⚙️ Configurazione

Gli intervalli sono configurabili via:
1. **Dashboard** → Settings → Agent Intervals
2. **MongoDB** → `system_config` collection
3. **Argomenti CLI** → `--interval 30`

---

## 📡 Dipendenze

Tutti gli agenti dipendono da:
- **MongoProxy** (`Orchestrator/src/mongo_proxy.py`)
- **MongoDB** (port 27017/28017)

Alcuni agenti richiedono anche:
- **Ollama** (AIAssistant, ForensicAnalyzer)
- **Qdrant** (AIAssistant per RAG)
- **SMTP** (CriticalAlert per email)

---

## 🔍 Pattern Matching (Watcher)

Il Watcher cerca pattern critici nei log:
- `ORA-*` - Errori Oracle
- `TNS-*` - Errori TNS
- `FATAL` - Errori fatali
- `ERROR` - Errori generici
- `deadlock` - Deadlock detection
