# Gateway Layer

## Scopo del progetto
Route commands between orchestrator and remote agents using Redis queues.

## Installazione e Setup
Redis is provided by docker-lab. Configure connection in Gateway/redis_config.

## Architettura
Queues:
- cmd_in: orchestrator to gateway to agent
- result_out: agent to gateway to orchestrator
Flow: Orchestrator -> Redis -> Gateway -> Agent -> Gateway -> Redis -> Orchestrator.

## Utilizzo
Start Redis from docker-lab and ensure the gateway process can reach it.
