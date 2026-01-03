# Redis Configuration

## Queues

```yaml
queues:
  cmd_in:
    name: "dba_ai:commands"
    type: "stream"
  result_out:
    name: "dba_ai:results"
    type: "stream"

connection:
  host: "localhost"
  port: 6379
  db: 0
  password: "${REDIS_PASSWORD}"
```

## Docker

```bash
docker run -d --name redis-dba-ai -p 6379:6379 redis:7-alpine
```
