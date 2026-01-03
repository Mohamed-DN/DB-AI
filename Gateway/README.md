# Gateway Layer (Layer 2)

The Gateway acts as the central routing hub between remote agents and the orchestrator.

## Components

### Python Gateway
- Routes commands from Orchestrator to Agents
- Collects results from Agents back to Orchestrator

### Redis Queues
| Queue | Direction | Purpose |
|-------|-----------|---------|
| `cmd_in` | Orchestrator → Agent | Commands to execute |
| `result_out` | Agent → Orchestrator | Execution results |

## Data Flow

```
Orchestrator → Redis (cmd_in) → Gateway → Agent (via SSH)
Agent → Gateway → Redis (result_out) → Orchestrator
```

## Configuration

See `redis_config/` for Redis connection settings.
