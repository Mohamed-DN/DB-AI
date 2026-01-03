# 📋 DailyAudit Agent

Esegue un controllo di conformità completo su tutti i database una volta al giorno.

## ⏱️ Schedule
- **Frequenza**: Giornaliero alle 02:00
- **Durata**: ~2-4 ore a seconda del numero di DB

## ✅ Controlli Eseguiti

### CENSIMENTO
- Completezza BAO/DL/Reperibilità
- Assegnazione gruppo SNOW
- Accessibilità gateway

### PERFORMANCE
- Cambio piano SQL nelle ultime 24h
- Esistenza restore point > X ore
- Dimensionamento connection pool

### CAPACITY
- Utilizzo tablespace vs soglia
- Utilizzo diskgroup vs massimo
- Conformità data retention

### BEST PRACTICES
- Tabelle non partizionate > 50GB
- Stats incrementali mancanti su tabelle grandi
- Utilizzo TEMP dedicata / Resource Manager

## 📤 Output

I risultati vengono scritti nella collezione `compliance_reports`.
