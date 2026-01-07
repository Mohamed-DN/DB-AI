# Container Monitoring

## Goal
Monitor Docker container health status and update database availability accordingly.

## Inputs
- Docker API or CLI
- Container naming convention: nexi-* for lab databases

## Execution Scripts
- `Agents/Watcher/main.py` - Container watcher agent
- `execution/check_container_health.py` - Health check utility

## Steps
1. List all running containers with `docker ps`
2. Filter for nexi-* and oracle-* containers
3. Check container health status
4. Update corresponding database document in MongoDB:
   - Container running: state.status = "UP"
   - Container stopped: state.status = "DOWN"
5. Trigger alert if status changed from UP to DOWN

## Edge Cases
- Docker daemon not running: log error, skip check
- Container restarting: wait for stable state before updating
- Network issue: container may be running but unreachable

## Learnings
- Use `docker inspect` for detailed health info
- Container names map to db_unique_name in MongoDB
- Gateway containers: maesdn-gateway provides routing
