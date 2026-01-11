# Collection: agent_runs

## Scopo del progetto
Track agent executions for audit and troubleshooting.

## Installazione e Setup
Created by backend or agents at runtime.

## Architettura
Fields include: agent, status, exit_code, started_at, finished_at, duration, output.

## Utilizzo
db.agent_runs.find({ agent: "scout" }).sort({ started_at: -1 }).limit(10)
