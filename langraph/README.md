# 🕸️ LangGraph

## 🎯 Scopo
Dedicata all'implementazione dei grafi di agenti usando LangGraph. Definisce i nodi, gli archi e la logica di controllo del flusso per task complessi che richiedono ragionamento a più step.

## 📂 File Manifest
- *(Placeholder)*: Questa directory è attualmente pronta per ospitare le definizioni dei grafi.
- **Futuri file previsti**: `graph.py` (definizione del grafo), `nodes/` (logica dei singoli step), `edges/` (condizioni di transizione).

## 🔗 Connessioni
- **Da `orchestrator`**: L'Orchestrator invocherà l'esecuzione di questi grafi per risolvere query complesse che l'LLM singolo non può gestire.
- **Uso di `llm`**: I nodi del grafo utilizzeranno i client LLM per prendere decisioni.
