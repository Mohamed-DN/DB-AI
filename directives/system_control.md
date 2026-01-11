# Directive: system_control

## Goal
Control global system state (RUNNING or PAUSED) and manage Docker Lab containers.

## Inputs
- **status**: "RUNNING" or "PAUSED"
- **MongoDB system_config**: Stores `global_status` key

## Outputs
- **global_status**: Updated in system_config
- **Docker Containers**: Started or stopped based on status

## Tools/Scripts
- `WebInterface/backend/main.py`: `/api/system/status` endpoint

## Edge Cases
- **Partial Container Failure**: Some containers may fail to start/stop
- **Agent Behavior**: All agents check `global_status` before each iteration

## API
```
GET /api/system/status   # Get current status
POST /api/system/status  # Set status
```

## Usage
```bash
# Pause system
curl -X POST http://localhost:9000/api/system/status \
  -H "Content-Type: application/json" \
  -d '{"status": true}'

# Resume system
curl -X POST http://localhost:9000/api/system/status \
  -H "Content-Type: application/json" \
  -d '{"status": false}'
```

## Notes
- When PAUSED, agents sleep but don't exit
- Frontend shows Pause/Play button in header
