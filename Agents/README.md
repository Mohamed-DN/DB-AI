# 🤖 Agents - Nexi DBA AI

Questa directory contiene gli **agenti autonomi** che eseguono le operazioni di monitoraggio.

## 📋 Lista Agenti

| Agente | Descrizione | Intervallo |
|--------|-------------|------------|
| [Scout](./Scout/) | Auto-discovery database in Docker | 60s |
| [CriticalAlert](./CriticalAlert/) | Invio email per alert critici | 30s |
| [Watcher](./Watcher/) | Streaming log e forensics | 10s |
| [CheckMK_Bridge](./CheckMK_Bridge/) | Importa metriche esterne | 60s |
| [Collector](./Collector/) | Raccolta metriche performance | 30s |

---

## 🛰️ Scout

**Scopo**: Rileva automaticamente database in container Docker.

**Come funziona**:
1. Esegue `docker ps` per trovare container
2. Filtra per label `db.type` (ORACLE, POSTGRES, etc.)
3. Verifica che il gateway del datacenter sia UP
4. Aggiorna `inventory_databases` in MongoDB
5. Genera alert `DB_DOWN` / `DB_RECOVERY` per cambi di stato

**Esecuzione**:
```powershell
python Agents/Scout/main.py --once  # Una volta
python Agents/Scout/main.py         # Continuo
```

---

## 🔔 CriticalAlert

**Scopo**: Invia email per alert critici.

**Come funziona**:
1. Polling MongoDB `monitoring_alerts` per alert `CRITICAL` non processati
2. Lookup contatto DBA da `inventory_databases`
3. Genera email HTML con template colorato
4. Invia via SMTP (Gmail) o salva in `emails/`
5. Marca alert come `processed: true`

**Configurazione**:
```env
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**Esecuzione**:
```powershell
python Agents/CriticalAlert/critical_alert.py --email admin@company.com --once
```

---

## 👁️ Watcher

**Scopo**: Streaming log container per rilevamento errori.

**Come funziona**:
1. Per ogni database UP, avvia `docker logs -f`
2. Bufferizza le ultime 100 righe per contesto
3. Rileva pattern critici: `ORA-*`, `TNS-*`, `FATAL`, etc.
4. Genera alert `DB_FORENSICS` con contesto
5. Il ForensicAnalyzer processa con AI

**Esecuzione**:
```powershell
python Agents/Watcher/main.py
```

---

## 🧠 ForensicAnalyzer

**Scopo**: Analisi AI degli errori rilevati.

**Come funziona**:
1. Polling `monitoring_alerts` per alert `DB_FORENSICS`
2. Estrae errore e contesto log
3. Invia a RAG pipeline (Qdrant + Ollama)
4. Riceve diagnosi con confidence score
5. Aggiorna alert con `ai_analysis`

**Esecuzione**:
```powershell
python Agents/Watcher/ai_analyzer.py --once
python Agents/Watcher/ai_analyzer.py --check  # Solo verifica dipendenze
```

---

## 📡 CheckMK_Bridge

**Scopo**: Importa metriche da monitoring esterno.

**Come funziona**:
1. Chiama CheckMK REST API (o simula dati)
2. Mappa hostname → `db_unique_name`
3. Estrae: CPU, RAM, Disk, host_state
4. Aggiorna `deep_observability.external_metrics` in MongoDB

**Configurazione**:
```env
CHECKMK_URL=http://checkmk-server/check_mk/api/v0
CHECKMK_USER=automation
CHECKMK_SECRET=your-secret
```

**Esecuzione**:
```powershell
python Agents/CheckMK_Bridge/main.py --once
```

---

## 📊 Collector

**Scopo**: Raccoglie metriche di performance dettagliate.

**Come funziona**:
1. Esegue query SQL su database target
2. Per Oracle: AWR, tablespaces, wait events
3. Per Postgres: pg_stat, pg_statio
4. Salva in `deep_observability` MongoDB

**Esecuzione**:
```powershell
python Agents/Collector/main.py --once
```

---

## 🔄 Ciclo di Vita

```
                    ┌─────────────┐
                    │   Scout     │ ──► Rileva database
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Watcher  │ │CheckMK   │ │Collector │
        │ (logs)   │ │ Bridge   │ │(metrics) │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │
             ▼            │            │
        ┌──────────┐      │            │
        │Forensic  │      │            │
        │Analyzer  │      │            │
        └────┬─────┘      │            │
             │            ▼            ▼
             └───────►  MongoDB  ◄─────┘
                           │
                           ▼
                    ┌─────────────┐
                    │CriticalAlert│ ──► Email
                    └─────────────┘
```

---

## 📝 Aggiungere un Nuovo Agente

1. Crea directory `Agents/NomeAgente/`
2. Crea `main.py` con struttura:
   ```python
   import argparse
   
   def run_once():
       # Logica agente
       pass
   
   def run_continuous(interval=30):
       while True:
           run_once()
           time.sleep(interval)
   
   if __name__ == "__main__":
       parser = argparse.ArgumentParser()
       parser.add_argument("--once", action="store_true")
       parser.add_argument("--interval", type=int, default=30)
       args = parser.parse_args()
       
       if args.once:
           run_once()
       else:
           run_continuous(args.interval)
   ```

3. Registra in `WebInterface/backend/main.py`:
   - Aggiungi a `agent_scripts` in `start_agent()`
   - Aggiungi a `agents` in `get_agents_status()`

4. Aggiungi configurazione intervallo in Settings HTML
