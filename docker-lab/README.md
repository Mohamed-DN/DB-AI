# 🧪 Ambiente di Laboratorio DBA AI

Questo ambiente Docker simula l'intera infrastruttura Nexi per test e sviluppo del sistema DBA AI.

## 📋 Architettura dell'Ambiente

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATOR (172.20.0.x)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   MongoDB   │  │    Redis    │  │   Ollama    │  │   Qdrant    │         │
│  │  :27017     │  │   :6379     │  │  :11434     │  │   :6333     │         │
│  │ 172.20.0.10 │  │ 172.20.0.11 │  │ 172.20.0.12 │  │ 172.20.0.13 │         │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│    GATEWAY MILANO (172.20.1.x)  │  │  GATEWAY BRATISLAVA (172.20.2.x)│
│  ┌─────────────────────────────┐│  │┌─────────────────────────────┐  │
│  │   SSH Gateway (porta 2221)  ││  ││   SSH Gateway (porta 2222)  │  │
│  │      172.20.1.1             ││  ││      172.20.2.1             │  │
│  └─────────────────────────────┘│  │└─────────────────────────────┘  │
│  ┌────────────┐ ┌────────────┐  │  │ ┌────────────┐ ┌────────────┐  │
│  │ PG PROD    │ │ PG DEV     │  │  │ │ PG PROD    │ │ PG DEV     │  │
│  │ payments   │ │ payments   │  │  │ │ cards      │ │ cards      │  │
│  │172.20.1.10 │ │172.20.1.11 │  │  │ │172.20.2.10 │ │172.20.2.11 │  │
│  └────────────┘ └────────────┘  │  │ └────────────┘ └────────────┘  │
└─────────────────────────────────┘  └─────────────────────────────────┘
```

## 🚀 Avvio Rapido

### Prerequisiti
- Docker Desktop installato
- Minimo 8GB RAM disponibili
- GPU NVIDIA (opzionale, per Ollama accelerato)

### Passaggi

1. **Clonare il repository**
   ```bash
   git clone https://github.com/ThomasNexi/Nexi_DB_AI.git
   cd Nexi_DB_AI/docker-lab
   ```

2. **Avviare l'ambiente**
   ```bash
   docker-compose up -d
   ```

3. **Verificare che tutti i container siano attivi**
   ```bash
   docker-compose ps
   ```

4. **Scaricare un modello LLM (prima volta)**
   ```bash
   docker exec -it nexi-ollama ollama pull llama3:8b
   ```

## 🔌 Porte e Connessioni

| Servizio | Porta Host | Indirizzo Interno | Credenziali |
|----------|------------|-------------------|-------------|
| MongoDB | 27017 | 172.20.0.10:27017 | admin / nexi2024 |
| Redis | 6379 | 172.20.0.11:6379 | - |
| Ollama | 11434 | 172.20.0.12:11434 | - |
| Qdrant | 6333 | 172.20.0.13:6333 | - |
| Gateway Milano | 2221 | 172.20.1.1:22 | service_audit / audit2024 |
| Gateway Bratislava | 2222 | 172.20.2.1:22 | service_audit / audit2024 |
| PG Milano PROD | - | 172.20.1.10:5432 | postgres / nexi2024 |
| PG Milano DEV | - | 172.20.1.11:5432 | postgres / nexi2024 |
| PG Bratislava PROD | - | 172.20.2.10:5432 | postgres / nexi2024 |
| PG Bratislava DEV | - | 172.20.2.11:5432 | postgres / nexi2024 |

## 🧪 Test di Connessione

### Test MongoDB
```bash
mongosh "mongodb://admin:nexi2024@localhost:27017"
```

### Test Gateway SSH
```bash
# Gateway Milano
ssh -p 2221 service_audit@localhost

# Gateway Bratislava
ssh -p 2222 service_audit@localhost
```

### Test PostgreSQL (attraverso Gateway)
```bash
# Connessione al Gateway
ssh -p 2221 service_audit@localhost

# Dal Gateway, connetti al database
psql -h pg-milano-prod.nexi.lab -U postgres -d payments_prod
```

### Test Ollama
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3:8b",
  "prompt": "Ciao, sono il DBA AI"
}'
```

## 🔄 Gestione dell'Ambiente

### Arresto
```bash
docker-compose down
```

### Arresto con rimozione dati
```bash
docker-compose down -v
```

### Visualizzare i log
```bash
# Tutti i servizi
docker-compose logs -f

# Servizio specifico
docker-compose logs -f mongodb
```

### Ricostruire i gateway (dopo modifiche)
```bash
docker-compose build gateway-milano gateway-bratislava
docker-compose up -d
```

## 📁 Struttura Directory

```
docker-lab/
├── docker-compose.yml    # Configurazione principale
├── gateway-ssh/
│   ├── Dockerfile        # Immagine gateway SSH
│   └── scripts/          # Script di test
└── README.md             # Questa documentazione
```

## 🏢 Mapping con Infrastruttura Nexi Reale

| Componente Lab | Corrispettivo Nexi |
|----------------|-------------------|
| gateway-milano | dbgec2 (Gateway Milano) |
| gateway-bratislava | dbgec3 (Gateway Bratislava) |
| pg-milano-prod | Database Oracle PROD Milano |
| pg-bratislava-prod | Database Oracle PROD Slovacchia |
| mongodb | Nuovo CMDB MongoDB |
| ollama | Server LLM interno |

## ⚠️ Note per Deploy Nexi

1. **Gateway**: In produzione usare chiavi SSH invece di password
2. **MongoDB**: Configurare replica set per alta disponibilità
3. **Ollama**: Verificare risorse GPU disponibili
4. **Rete**: Sostituire gli IP con quelli reali dell'infrastruttura
