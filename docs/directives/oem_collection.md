# 📊 OEM Collection Directive

> Standard Operating Procedure for Oracle Enterprise Manager data ingestion.

---

## 🎯 AI Context

```yaml
Purpose: Collect deep Oracle database metrics from OEM REST API
Agent: OEM_Collector
Location: api_agents/workers/OEM_Collector/
Trigger: API endpoint POST /api/action/oem-collect
Output: MongoDB collection (oem_metrics), VictoriaMetrics
```

---

## 📋 Procedure

### 1. Authentication
- Connect to OEM REST API using stored credentials
- Credentials stored in `gateway_config.oem_instances[]`
- Auth type: Basic Authentication over HTTPS

### 2. Target Discovery
- Fetch all Oracle targets from `/em/websvcs/restful/extws/cloudservices/ssa/cfw/v2/targets`
- Filter by target type: `oracle_database`, `oracle_pdb`
- Cache target list in MongoDB

### 3. Metrics Collection
- For each target, fetch performance metrics:
  - Active Sessions
  - CPU Usage
  - I/O Throughput
  - Tablespace Usage
  - Wait Events

### 4. Data Storage
- Write to MongoDB: `oem_metrics` collection
- Push to VictoriaMetrics for time-series analysis
- Update `inventory_databases` with OEM metadata

---

## ⚙️ Configuration

```yaml
# In gateway_config collection
oem_instances:
  - name: "Production OEM"
    url: "https://oem.nexi.lab:7803/em"
    username: "sysman"
    check_ssl: true
    enabled: true
```

---

## 🔗 Related

- [OEM_Collector Agent](../../api_agents/workers/OEM_Collector/oem_collector.py)
- [OEM Dashboard](../../web/dashboard/src/components/Admin/OEM/OEMDashboard.tsx)
- [Metric Collection Directive](./metric_collection.md)
