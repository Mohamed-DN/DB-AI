# Directive: checkmk_sync

## Goal
Import monitoring data from external CheckMK instance.

## Inputs
- **CheckMK API**: URL and credentials
- **Hosts**: List of hosts to sync

## Outputs
- **inventory_hosts**: Synced host information
- **external_metrics**: CheckMK metrics stored

## Tools/Scripts
- `Agents/CheckMK_Bridge/main.py`: Sync agent

## Edge Cases
- **API Unreachable**: Retry with exponential backoff
- **Rate Limiting**: Respect CheckMK API limits
- **Schema Mismatch**: Log and skip incompatible fields

## API
```
# No direct API - runs as background agent
```

## Usage
```powershell
# Requires CheckMK configuration
export CHECKMK_URL=https://checkmk.example.com
export CHECKMK_USER=automation
export CHECKMK_SECRET=your_secret

python Agents/CheckMK_Bridge/main.py --once
```

## Notes
- Currently focused on host inventory sync
- Metrics import is planned for future release
