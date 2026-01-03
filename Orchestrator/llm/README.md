# LLM Integration

Local Large Language Model for AI processing.

## Technology

- **Ollama** for local inference
- Models: Llama3, Mistral, CodeLlama

## Configuration

```yaml
llm:
  provider: "ollama"
  base_url: "http://localhost:11434"
  models:
    chat: "llama3:8b"
    code: "codellama:7b"
    embed: "nomic-embed-text"
```

## Use Cases

- Natural language query processing
- Code/SQL generation
- Incident analysis
- Runbook suggestions
