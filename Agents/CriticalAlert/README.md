# 🚨 CriticalAlert Agent

Agente real-time che monitora errori critici e attiva alert immediati.

## ⏱️ Schedule
- **Frequenza**: Continuo (polling ogni 30 secondi)
- **Sorgente**: Checkmk + controlli diretti DB

## 🔴 Condizioni Critiche Monitorate

| Condizione | Severità | Azione |
|------------|----------|--------|
| Database DOWN | CRITICAL | Email BAO + DL |
| Tablespace > 95% | CRITICAL | Email BAO |
| Data Guard LAG > 1 ora | HIGH | Email DL |
| Backup fallito | HIGH | Email DL |
| Sessione bloccante > 30 min | MEDIUM | Log + Alert |

## 🔗 Integrazione

- Legge da `monitoring_alerts` (sync Checkmk)
- Interroga CMDB per info contatti
- Invia email via SMTP
