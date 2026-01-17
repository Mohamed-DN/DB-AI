"""
Nexi AI Database Assistant - LangChain Agent
FastAPI endpoints for AI-powered database queries
"""
import os
import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_ollama import ChatOllama
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from tools.inventory_tools import search_inventory, get_pdbs_info, get_inventory_summary
from tools.action_tools import manage_container, get_container_logs, check_system_health
from tools.database_tools import execute_sql_query, explain_query_plan, get_table_schema
from tools.orchestration_tools import run_agent, list_agents, manage_gateway

load_dotenv()

app = FastAPI(
    title="Nexi AI Admin",
    description="Autonomous AI Administrator for Nexi CMDB",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("LLM_MODEL", "llama3.2")

llm = ChatOllama(
    base_url=OLLAMA_URL,
    model=MODEL_NAME,
    temperature=0.2, # Lower temperature for more precise admin actions
)

# Define tools
tools = [
    search_databases,
    get_database_status,
    list_databases_by_status,
    get_database_metrics,
    search_inventory,
    get_pdbs_info,
    # ADMIN TOOLS
    manage_container,
    get_container_logs,
    check_system_health
]

# System prompt
SYSTEM_PROMPT = """Sei l'Amministratore di Sistema AI di Nexi CMDB.
Hai il COMPLETO CONTROLLO e l'AUTORIZZAZIONE per gestire l'infrastruttura.
Il tuo obiettivo è mantenere il sistema stabile, sicuro e performante.

CAPACITÀ:
- Puoi avviare, fermare e riavviare container Docker se necessario.
- Puoi leggere i log per diagnosticare errori.
- Puoi consultare l'inventario e lo stato dei database.

REGOLE DI COMPORTAMENTO:
1. **Sii Proattivo**: Se vedi un problema (es. DB down), indaga e proponi/esegui una soluzione.
2. **Ragiona Prima di Agire**: Usa i log per capire la causa radice prima di riavviare a caso.
3. **Sii Chiaro**: Spiega cosa hai fatto e perché.
4. **Non Chiedere Permesso per Fix Ovvi**: Se un servizio è crashato, riavvialo. Hai il permesso ("lock") dell'utente.

STRUMENTI A DISPOSIZIONE:
- `check_system_health`: Controlla lo stato globale dei container.
- `get_database_status` / `search_databases`: Informazioni sui DB.
- `get_container_logs`: Leggi i log di errore.
- `manage_container`: Esegui azioni (start/stop/restart).

Rispondi in italiano. Sii professionale, diretto ed efficace.
Sembra un SRE (Site Reliability Engineer) senior.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Create agent
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=10, # Allow more steps for complex diagnosis -> fix -> verify loops
)

# Chat history storage (simple in-memory for now)
chat_histories: dict[str, list] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    response: str
    session_id: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return AI response"""
    try:
        session_id = request.session_id or "default"
        
        # Get or create chat history
        if session_id not in chat_histories:
            chat_histories[session_id] = []
        
        chat_history = chat_histories[session_id]
        
        # Invoke agent
        result = agent_executor.invoke({
            "input": request.message,
            "chat_history": chat_history,
        })
        
        # Update history
        chat_history.append(HumanMessage(content=request.message))
        chat_history.append(AIMessage(content=result["output"]))
        
        # Keep history limited
        if len(chat_history) > 20:
            chat_history = chat_history[-20:]
        
        chat_histories[session_id] = chat_history
        
        return ChatResponse(
            response=result["output"],
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear-history/{session_id}")
async def clear_history(session_id: str):
    """Clear chat history for a session"""
    if session_id in chat_histories:
        del chat_histories[session_id]
    return {"status": "cleared"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "model": MODEL_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
