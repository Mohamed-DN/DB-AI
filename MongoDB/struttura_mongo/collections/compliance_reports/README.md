# Compliance Reports Collection

Stores daily audit results and remediation tracking.

## Purpose
- Track compliance status over time
- Document issues and remediation
- Generate reports for management

## Indexes

```javascript
db.compliance_reports.createIndex({ "report_date": -1 }, { name: "idx_report_date" });
db.compliance_reports.createIndex({ "issues.db_unique_name": 1 }, { name: "idx_issues_db" });
db.compliance_reports.createIndex({ "issues.remediation_status": 1, "issues.severity": 1 }, { name: "idx_open_issues" });
```
