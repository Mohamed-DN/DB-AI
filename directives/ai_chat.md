# AI Chat Operations

## Goal
Handle AI chat interactions using LangChain agent backed by Ollama LLM.

## Inputs
- User message from frontend
- Current LLM model selection
- Database context from MongoDB

## Execution Scripts
- `Agents/AIAssistant/main.py` - FastAPI AI agent server
- `Agents/AIAssistant/tools/database_tools.py` - Database query tools
- `Agents/AIAssistant/tools/inventory_tools.py` - Inventory search tools

## Steps
1. Receive message from frontend at `/api/chat`
2. Backend proxies to AIAssistant at `http://localhost:8001/chat`
3. LangChain agent processes with tools:
   - search_databases: Find databases by name/engine
   - get_database_status: Get current status
   - get_database_metrics: Get performance metrics
4. Return AI response to frontend

## Configuration
- LLM_MODEL: deepseek-r1:14b (default)
- OLLAMA_BASE_URL: http://localhost:11434
- Available models: qwen3:30b-a3b, mistral-small3.1:24b, deepseek-r1:14b, qwen3:14b, llama3.2:8b

## Edge Cases
- Ollama not running: return error message
- Model not loaded: attempt to load, inform user if fails
- GPU memory exhausted: suggest smaller model
