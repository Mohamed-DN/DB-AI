"""
Nexi AI Database Assistant - LangGraph Agent
FastAPI endpoints for AI-powered database queries
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Services
from api_agents.workers.aiassistant.services.tool_registry import ToolRegistry
from api_agents.workers.aiassistant.services.rag_service import RAGService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(override=True)

# Global State
tool_registry = None
rag_service = None
agent_app = None # Replaces agent_executor

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.1:8b")

llm = ChatOllama(
    base_url=OLLAMA_BASE_URL,
    model=MODEL_NAME,
    temperature=0
)

# Chat History Storage (Simple In-Memory for MVP)
chat_histories = {}

SYSTEM_PROMPT = """You are NexiDB, an expert Database Administrator AI.
Your goal is to help users manage, debug, and optimize Oracle and PostgreSQL databases.
You have access to real-time inventory tools, execution tools, and a RAG knowledge base.

Guidelines:
1. ALWAYS verify the database status before suggesting actions.
2. If an error is technical (e.g. ORA-00600), use the 'search_knowledge_base' tool.
3. Be concise and professional.
4. If you execute a query, summarize the results clearly.
"""

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global tool_registry, rag_service, agent_app
    
    # Init Mongo
    mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    db = mongo_client["Nexi_DB_AI"]
    
    # Init Services
    tool_registry = ToolRegistry(db)
    rag_service = RAGService()
    
    # Load Tools
    # Load Tools
    print("Loading tools from Registry...")
    tools = await tool_registry.get_tools()
    print(f"Loaded {len(tools)} tools: {[t.name for t in tools]}")
    
    # RAG Tool Definition
    from langchain_core.tools import StructuredTool
    
    class RAGInput(BaseModel):
        query: str = Field(description="The question to search usage documentation for")
        domain: Optional[str] = Field(description="Optional domain filter (e.g. 'oracle', 'postgres')")

    async def search_knowledge_base(query: str, domain: str = None):
        """Search the knowledge base for runbooks and SOPs."""
        return await rag_service.search(query, domain)

    rag_tool = StructuredTool.from_function(
        func=None,
        coroutine=search_knowledge_base,
        name="search_knowledge_base",
        description="Search technical documentation, runbooks, and SOPs. Use this when you don't know how to solve a specific database error.",
        args_schema=RAGInput
    )
    
    tools.append(rag_tool)
    
    # Init Agent (LangGraph)
    # Using create_react_agent which is the modern standard for tool-calling agents
    agent_app = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)
    
    yield
    
    # Shutdown
    mongo_client.close()

app = FastAPI(
    title="Nexi AI Admin",
    description="Autonomous AI Administrator for Nexi CMDB",
    version="2.2.0", # Bumped version for LangGraph
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return AI response"""
    if not agent_app:
            raise HTTPException(status_code=503, detail="Agent initializing...")
            
    try:
        session_id = request.session_id or "default"
        if session_id not in chat_histories:
            chat_histories[session_id] = []
        
        # Prepare LangGraph input (list of messages)
        # We include history + new message
        # LangGraph ReAct agent manages state, but here we feed strictly the "messages" key
        # For simplicity in this stateless pass: we send history + current message
        
        messages = chat_histories[session_id] + [HumanMessage(content=request.message)]
        
        # Invoke Agent
        result = await agent_app.ainvoke({"messages": messages})
        
        # Extract response
        # The result state contains "messages". The last one is the AI response.
        final_messages = result["messages"]
        last_message = final_messages[-1]
        response_text = last_message.content
        
        # Update history
        chat_histories[session_id].append(HumanMessage(content=request.message))
        chat_histories[session_id].append(AIMessage(content=response_text))
        
        # Limit history
        if len(chat_histories[session_id]) > 20: 
            chat_histories[session_id] = chat_histories[session_id][-20:]
        
        return ChatResponse(response=response_text, session_id=session_id)
    except Exception as e:
        logger.error(f"Chat Error: {e}", exc_info=True)
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
