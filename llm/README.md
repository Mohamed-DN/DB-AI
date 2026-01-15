# 🗣️ Large Language Models (LLM)

## 🎯 Scopo
Centralizza la configurazione e i client per i modelli di linguaggio (es. Ollama, OpenAI, Anthropic). Isola la logica di "prompting" e "inference".

## 📂 File Manifest
- **`client/`**: (Directory) Wrapper Python per comunicare con i provider LLM (gestione retry, streaming).
- **`config/`**: (Directory) File di configurazione (es. `llm_config.py`) per definire modelli, temperature e endpoint.

## 🔗 Connessioni
- **Da `orchestrator`**: L'Orchestrator importa questi client per eseguire le chiamate di inferenza.
- **Verso Esterno**: Comunica con i servizi LLM (es. Ollama locale sulla porta 11434 o API esterne).
