# Directive: ai_chat

## Scopo del progetto
Provide AI chat over inventory and alerts.

## Installazione e Setup
Ollama and MongoDB must be running. Configure OLLAMA_HOST.

## Architettura
- API: POST /api/chat
- Model selection: GET /api/llm/current and POST /api/llm/switch
- Context: inventory_databases and monitoring_alerts

## Utilizzo
Use the AI Chat panel in the UI or call POST /api/chat.
