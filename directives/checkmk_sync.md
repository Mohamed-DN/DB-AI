# CheckMK Sync

## Goal
Synchronize database inventory and status with CheckMK monitoring system.

## Inputs
- Database inventory from MongoDB
- CheckMK API credentials

## Execution Scripts
- `Agents/CheckMK_Bridge/main.py` - Bridge agent

## Steps
1. Query MongoDB for all databases
2. For each database, sync to CheckMK:
   - Create/update host in CheckMK
   - Create service checks for database
   - Set thresholds based on DB type
3. Retrieve status from CheckMK
4. Update MongoDB with CheckMK status

## Configuration
- CHECKMK_URL: CheckMK server URL
- CHECKMK_USER: API username
- CHECKMK_SECRET: API secret
- CHECKMK_SITE: Site name

## Edge Cases
- CheckMK API unavailable: log error, continue offline
- Database not in CheckMK: create new host entry
- Stale data: sync every 120 seconds (configurable)

## Learnings
- CheckMK integration is optional - system works without it
- Focus on critical alerts even if CheckMK is down
