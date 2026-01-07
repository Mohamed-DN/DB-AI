# System Control

## Goal
Manage system-wide operations: pause/resume monitoring, start/stop containers, run auto-discovery.

## Inputs
- User action from frontend buttons
- System status from MongoDB

## Execution Scripts
- `execution/start_stop_containers.py` - Container management
- `scripts/start-all.ps1` - Start all services
- `scripts/stop-all.ps1` - Stop all services

## Actions

### Pause System
1. Set `system.status = "PAUSED"` in MongoDB
2. Stop all nexi-* containers (except MongoDB)
3. Update frontend status indicator

### Resume System
1. Set `system.status = "RUNNING"` in MongoDB
2. Start all nexi-* containers
3. Trigger immediate health check
4. Update frontend status indicator

### Auto-Discovery
1. Run `execution/discover_docker_databases.py`
2. For each discovered database:
   - Run `execution/register_database.py`
3. Refresh inventory in frontend

## API Endpoints
- GET `/api/system/status` - Get current status
- POST `/api/system/status` - Set status (RUNNING/PAUSED)
- POST `/api/action/scan` - Trigger auto-discovery

## Edge Cases
- Container start failure: log error, return partial results
- MongoDB unavailable: cannot change system status
- Concurrent pause/resume: use mutex lock
