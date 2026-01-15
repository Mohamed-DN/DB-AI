# Collector Steps

## Scopo del progetto
Describe the internal steps of the Collector agent.

## Installazione e Setup
See Agents/Collector/README.md.

## Architettura
1) Load inventory targets from MongoDB
2) Resolve running containers and host details
3) Collect docker stats or remote metrics
4) Normalize metrics
5) Update inventory_databases state.metrics

## Utilizzo
Use this checklist when modifying collector logic or adding new extractors.
