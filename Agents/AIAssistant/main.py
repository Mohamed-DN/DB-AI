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

from tools.database_tools import (
    search_databases,
    get_database_status,
    list_databases_by_status,
    get_database_metrics
)
from tools.inventory_tools import (
    search_inventory,
    get_pdbs_info
)

load_dotenv()

app = FastAPI(
    title="Nexi AI Assistant",
    description="LangChain-powered AI for database management",
    version="1.0.0"
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
    temperature=0.1,
)

# Define tools
tools = [
    search_databases,
    get_database_status,
    list_databases_by_status,
    get_database_metrics,
    search_inventory,
    get_pdbs_info,
]

# System prompt
SYSTEM_PROMPT = """Sei l'assistente AI di Nexi CMDB (Configuration Management Database).
Il tuo compito è aiutare gli utenti a gestire e monitorare i database Oracle e PostgreSQL.

Hai accesso ai seguenti strumenti:
- search_databases: Cerca database per nome
- get_database_status: Ottieni lo stato di un database specifico
- list_databases_by_status: Lista tutti i database con un certo stato (UP, DOWN, WARNING)
- get_database_metrics: Ottieni le metriche di un database
- search_inventory: Cerca nell'inventario MongoDB
- get_pdbs_info: Ottieni informazioni sui PDB di un database Oracle

Rispondi sempre in italiano a meno che l'utente non scriva in inglese.
Sii conciso ma completo nelle risposte.
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
    max_iterations=5,
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
