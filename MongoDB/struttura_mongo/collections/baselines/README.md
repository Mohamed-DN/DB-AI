# Collection: baselines

## Scopo del progetto
Store baseline metrics for comparison and drift detection.

## Installazione e Setup
Created by collector or analysis workflows.

## Architettura
Fields include: db_unique_name, metric, baseline_value, window, updated_at.

## Utilizzo
db.baselines.find({ db_unique_name: "DB1" })
