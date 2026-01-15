# Collection: compliance_reports

## Scopo del progetto
Store audit and compliance results for databases.

## Installazione e Setup
Created by DailyAudit or analysis workflows.

## Architettura
Fields include: db_unique_name, rule_id, status, findings, created_at.

## Utilizzo
db.compliance_reports.find({ status: "FAIL" }).limit(20)
