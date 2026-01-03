# Best Practices Module

Enforces Oracle/Postgres best practices and sends remediation requests.

## Checks

### Partitioning
- Tables > 50GB without partitioning
- Tables > 100GB (critical)
- Incremental stats on partitioned tables

### Indexing
- Missing indexes on FK relationships
- Full table scans on large tables
- Index usage statistics

### Bind Variables
- Queries with literals instead of binds
- High version count in shared pool

### Environment Validation
- Staging validation before PROD
- Configuration drift detection

## Actions
- Generate email to BAO with remediation requests
- Link to CMDB contact info
- Track remediation status
