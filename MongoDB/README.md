# MongoDB CMDB - Python Implementation

Python package for interacting with the CMDB MongoDB database.

## Setup

### 1. Start MongoDB
```bash
docker-compose up -d
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Initialize
```bash
cd scripts
python create_indexes.py
python seed_sample_data.py
python test_connection.py
```

## Usage

```python
from src.repositories import InventoryRepository, ServiceRepository

# Find databases
repo = InventoryRepository()
oracle_dbs = repo.find_by_engine("ORACLE")
high_usage = repo.find_with_tablespace_above_threshold(90)

# Get BAO contact
svc_repo = ServiceRepository()
bao = svc_repo.get_bao_for_database("NZSEP")
```

## Structure

- `src/connection.py` - MongoDB connection
- `src/models/` - Pydantic models
- `src/repositories/` - Data access layer
- `scripts/` - Initialization scripts
