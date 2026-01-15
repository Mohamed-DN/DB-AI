# LLM Module

## Scopo del progetto
Manage LLM configuration and model switching.

## Installazione e Setup
Set OLLAMA_HOST in .env. Pull models with scripts/pull_models.ps1.

## Architettura
- llm/ollama_client.py: client calls
- config/llm_config.py: model list and defaults

## Utilizzo
API endpoints:
- GET /api/llm/current
- POST /api/llm/switch { "model": "..." }
