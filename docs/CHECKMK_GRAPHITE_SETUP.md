# CheckMK Raw Edition → VictoriaMetrics via Graphite

Questa guida spiega come configurare CheckMK Raw Edition per inviare metriche a VictoriaMetrics usando il protocollo **Graphite**.

## Architettura

```
┌─────────────────┐    Graphite (2003)    ┌─────────────────────┐
│  CheckMK Raw    │ ─────────────────────► │   VictoriaMetrics   │
│    Edition      │                        │  (Graphite bridge)  │
└─────────────────┘                        └──────────┬──────────┘
                                                      │ PromQL
                                                      ▼
                              ┌─────────────┐         ┌─────────────┐
                              │   Grafana   │ ◄───────│   Prometheus│
                              │ (Dashboard) │         │  (optional) │
                              └─────────────┘         └─────────────┘
```

## Configurazione VictoriaMetrics

VictoriaMetrics è già configurato per ricevere dati Graphite sulla **porta 2003**.

```yaml
# docker-compose-v2.yml
victoriametrics:
  command:
    - '--graphiteListenAddr=:2003'  # Abilita Graphite
```

## Configurazione CheckMK Raw Edition

### Passo 1: Accedi a CheckMK
1. Vai su: `http://localhost:8080/nexi_monitor`
2. Login: `cmkadmin` / `nexi2024`

### Passo 2: Configura Export Graphite
1. Vai su **Setup** → **General** → **Global Settings**
2. Cerca **"Metrics export"** o **"Graphite"**
3. Abilita **"Send metrics to Graphite"**

### Passo 3: Impostazioni Graphite
| Parametro | Valore |
|-----------|--------|
| **Protocol** | `Graphite plaintext` |
| **Address** | `victoriametrics.nexi.lab` |
| **Port** | `2003` |
| **Prefix** | `checkmk` (opzionale) |

> ⚠️ Se usi Docker, l'hostname è `victoriametrics` (nome del container)

### Passo 4: Activate Changes
Clicca su **"Activate on selected sites"** per applicare le modifiche.

## Verifica Funzionamento

### Test connettività Graphite
```bash
# Invia metrica test
echo "test.metric 42 $(date +%s)" | nc -q0 localhost 2003

# Verifica in VictoriaMetrics
curl "http://localhost:8428/api/v1/query?query=test_metric"
```

### Query in Grafana
Le metriche CheckMK saranno disponibili come:
- `checkmk_*` (con prefix)
- Es: `checkmk.host.service.metric`

### Esempio Query PromQL
```promql
# CPU usage da CheckMK
checkmk_CPU_usage

# Memoria
checkmk_Memory_used

# Tutti i servizi critici
checkmk_service_state == 2
```

## Troubleshooting

### "Connection refused"
- Verifica che VictoriaMetrics sia avviato: `docker ps | grep victoriametrics`
- Verifica porta: `netstat -an | findstr 2003`

### Metriche non visibili
- Aspetta 60 secondi (intervallo CheckMK)
- Verifica logs: `docker logs nexi-victoriametrics 2>&1 | tail -20`

### Formato metriche Graphite
VictoriaMetrics converte automaticamente:
```
checkmk.host.cpu.usage 85.5 1705855200
         ↓
{__name__="checkmk_host_cpu_usage", host="host", metric="cpu"}
```
