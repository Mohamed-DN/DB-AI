# 🕵️ Agenti SADA

Agenti AI per la gestione automatizzata dei database enterprise.

## 📋 Lista Agenti

| Agente | Schedule | Descrizione |
|--------|----------|-------------|
| **Scout** | 5 min | Scoperta nuovi database via process scanning |
| **Collector** | Giornaliero | Estrazione profonda (configurazione, storage, metriche) |
| **Monitor** | 1 min | Sincronizzazione alert Checkmk |
| **DailyAudit** | Giornaliero 02:00 | Controllo conformità completo |
| **CriticalAlert** | Real-time | Rilevamento errori critici |

## 🏗️ Struttura

```
Agents/
├── Scout/          # Scoperta
├── Collector/      # Estrazione profonda
├── Monitor/        # Sync Checkmk
├── DailyAudit/     # Audit giornaliero
├── CriticalAlert/  # Alert critici
└── main.py         # Orchestratore
```

## 🚀 Utilizzo

```bash
# Collector - raccolta dati da host specifici
cd Collector
python main.py --targets host1.local host2.local --gateway dbgec2

# DailyAudit - esegui audit manuale
cd DailyAudit
python main.py --run-now
```
