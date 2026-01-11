# Directive: ai_chat

## Goal
Provide AI-powered chat interface for database queries and actions.

## Inputs
- **User Message**: Natural language query
- **inventory_databases**: Context for DB-related queries
- **monitoring_alerts**: Context for alert queries
- **Ollama LLM**: For response generation

## Outputs
- **AI Response**: Natural language answer
- **Actions**: Optional database operations (connect, query, etc.)

## Tools/Scripts
- `Agents/AIAssistant/tools/`: Tool implementations
- `Orchestrator/rag/`: RAG pipeline

## Edge Cases
- **LLM Timeout**: Return error message after 60s
- **Invalid Action**: Validate before execution
- **Context Too Large**: Truncate to fit model context window

## API
```
POST /api/chat   # Send message
GET /api/llm/models   # List available models
POST /api/llm/switch  # Switch model
```

## Usage
```bash
curl -X POST http://localhost:9000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all PostgreSQL databases"}'
```

## Capabilities
- Query inventory ("list databases", "show alerts")
- Execute actions ("connect to DB X", "run discovery")
- Analyze issues ("why is DB X down?")

## Models
Default: `qwen2.5:7b`
Alternatives: See `/api/llm/models`
