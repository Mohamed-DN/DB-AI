# Data Extraction Schema

## Scopo del progetto
Describe how raw metrics and configuration data are extracted and normalized.

## Installazione e Setup
Use Scout and Collector agents. See Agents/Collector/README.md.

## Architettura
- Scout discovers targets and inserts inventory stubs
- Collector enriches inventory with metrics
- CheckMK Bridge imports external metrics
- CriticalAlert writes alert documents

## Utilizzo
Use this document when adding new extractors or data sources.
