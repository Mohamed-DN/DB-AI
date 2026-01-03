# SADA-SCOUT Agent

The **Scout** agent is designed to be lightweight and fast. It monitors the infrastructure for new services.

## Functions

1. **Process Scanning**: Uses `ps -ef` and `netstat` to identify running services.
2. **AI Analysis**: Uses local LLM (Ollama) to interpret process signatures.
3. **Queueing**: Pushes identified targets to the `Discovery_Queue` collection in MongoDB.

## Key Files
- *(To be implemented)*
