"""
Nexi AI CMDB - API Gateway
FastAPI application with modular router architecture.

Version: 3.1.0
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import configuration
from .config import ALLOWED_ORIGINS

# Import routers
from .routers.inventory import router as inventory_router
from .routers.alerts import router as alerts_router
from .routers.agents import router as agents_router
from .routers.llm import router as llm_router
from .routers.system import router as system_router
from .routers.metrics import router as metrics_router
from .routers.emails import router as emails_router
from .routers.connection import router as connection_router
from .routers.tasks import router as tasks_router
from .routers.workflows import router as workflows_router

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Nexi AI CMDB",
    version="3.1.0",
    description="AI-Powered Database Management - Modular Architecture",
    docs_url="/docs",
    redoc_url="/redoc"
)

# =============================================================================
# Middleware
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# =============================================================================
# Include Routers
# =============================================================================

# System router has root endpoint, include without prefix
app.include_router(system_router, tags=["System"])

# API routers with /api prefix
app.include_router(inventory_router, prefix="/api", tags=["Inventory"])
app.include_router(alerts_router, prefix="/api", tags=["Alerts"])
app.include_router(agents_router, prefix="/api", tags=["Agents"])
app.include_router(llm_router, prefix="/api", tags=["LLM"])
app.include_router(metrics_router, prefix="/api", tags=["Metrics"])
app.include_router(emails_router, prefix="/api", tags=["Emails"])
app.include_router(connection_router, prefix="/api", tags=["Connection"])
app.include_router(tasks_router, prefix="/api", tags=["Tasks"])
app.include_router(workflows_router, prefix="/api", tags=["Workflows"])

# =============================================================================
# Startup Event
# =============================================================================

@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("🚀 Nexi AI CMDB v3.1.0 - Modular Architecture")
    print(f"📁 Routers loaded: inventory, alerts, agents, llm, system, metrics, emails, connection, tasks, workflows")
    print(f"🌐 CORS Origins: {ALLOWED_ORIGINS}")
    print("=" * 60)

# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    import uvicorn
    
    port = int(os.getenv("BACKEND_PORT", 9000))
    print(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
