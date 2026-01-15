# 🛠️ Operations & Infrastructure (Ops)

## 🎯 Scopo
Raggruppa gli strumenti per la gestione del ciclo di vita del progetto, l'ambiente di laboratorio Docker e gli script di automazione.

## 📂 File Manifest
- **`docker-lab/`**: (Directory) Definizioni Docker Compose per l'ambiente di simulazione (Oracle, Postgres, MongoDB, LLM).
- **`scripts/`**: (Directory) Script PowerShell/Bash per setup (`setup_v2.ps1`), avvio e cleanup.
- **`gateway/`**: (Directory) Configurazioni per i container "Gateway SSH" simulati.

## 🔗 Connessioni
- **Root**: Gli script qui contenuti vengono spesso eseguiti dalla root del progetto per inizializzare l'intero stack.
