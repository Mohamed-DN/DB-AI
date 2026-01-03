# SADA Collector Agent

Deep extraction agent for populating the CMDB with Oracle/Postgres data.

## Features
- SSH via Gateway (bastion) or direct
- Oracle data extraction (version, patches, storage, RAC, DataGuard)
- System data extraction (OS, CPU, memory)
- CMDB transformation and update

## Setup
```bash
pip install -r requirements.txt
cp config/config.yaml.example config/config.yaml
# Edit config.yaml with your gateway credentials
```

## Usage
```bash
# Collect from specific hosts
python main.py --targets host1.local host2.local --gateway dbgec2

# Direct connection (no gateway)
python main.py --targets host1.local --no-gateway
```

## Structure
```
Collector/
├── main.py                 # Entry point
├── requirements.txt
├── config/
│   └── config.yaml.example
├── src/
│   ├── ssh_connection.py   # Gateway/SSH helper
│   ├── cmdb_updater.py     # CMDB transformation
│   └── extractors/
│       ├── oracle_extractor.py
│       └── system_extractor.py
└── resources/
    └── oracle_scripts/     # SQL scripts
```

## SQL Queries Executed
- Database info (v$database, v$instance)
- Oracle Home and patches
- ASM diskgroups
- Tablespaces
- RAC nodes
- Data Guard status
- Licensed features
