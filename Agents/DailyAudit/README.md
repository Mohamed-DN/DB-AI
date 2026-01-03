# DailyAudit Agent

Runs once per day to perform a comprehensive compliance check across all databases.

## Schedule
- **Frequency**: Daily at 02:00 AM
- **Duration**: ~2-4 hours depending on DB count

## Checks Performed

### CENSIMENTO (Census)
- BAO/DL/Reperibilità completeness
- SNOW group assignment
- Gateway accessibility

### PERFORMANCE
- SQL plan changes in last 24h
- Restore point existence > X hours
- Connection pool sizing

### CAPACITY
- Tablespace usage vs threshold
- Diskgroup usage vs max
- Data retention compliance

### BEST PRACTICES
- Non-partitioned tables > 50GB
- Missing incremental stats on large tables
- Dedicated TEMP/Resource Manager usage

## Output
Writes results to `compliance_reports` collection.
