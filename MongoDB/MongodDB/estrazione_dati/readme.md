L'Architettura
Il flusso dei dati sarà questo:

Collector (Python): Si connette via SSH ai server o via JDBC/ODBC ai DB. Esegue comandi grezzi (lscpu, SELECT * FROM...).

Raw Data: Ottieni stringhe di testo non strutturate o parzialmente strutturate.

LLM Processor (The Brain): Prende il testo grezzo + lo Schema JSON desiderato e "mappa" i dati.

MongoDB Loader: Salva il JSON pulito.