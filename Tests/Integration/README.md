# Integrazione e Scenari di Test

Questa directory contiene script per testare le capacità avanzate del CMDB AI-Driven.

## Contenuto

- `run_advanced_scenario.ps1`: Script PowerShell che esegue un test end-to-end completo:
    1.  **Pulisce** l'ambiente (rimuove DB di test, ripristina lo stato).
    2.  **Deploya** un nuovo Database (`nexi-pg-milano-stg`) per testare l'Auto-Discovery.
    3.  **Esegue Scout Agent**: Rileva automaticamente tutti i DB attivi (incluso il nuovo) e popola l'Inventory su MongoDB.
    4.  **Simula Disastro**: Arresta forzatamente `nexi-pg-bratislava-dev`.
    5.  **Esegue CriticalAlert**: Rileva che Bratislava è DOWN.
    6.  **Esegue AI Orchestrator**: 
        - Analizza gli alert con Llama 3.
        - Genera e invia email di notifica.
        - Salva le email generate in `emails/` per verifica.

## Come Eseguire

```powershell
.\run_advanced_scenario.ps1
```

## Verifica Risultati

- Controllare la console per i log dell'AI ("Run ONCE").
- Controllare la cartella `emails/` nella root del progetto per vedere i file `.html` delle email generate.
