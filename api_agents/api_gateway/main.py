"""
M-DN AI CMDB - API Gateway
FastAPI application with modular router architecture.

Version: 3.2.0 - With Authentication
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import configuration
try:
    from api_agents.api_gateway.config import ALLOWED_ORIGINS
    print("[OK] Config imported")

    # Import routers
    from api_agents.api_gateway.routers.inventory import router as inventory_router
    print("[OK] Inventory Router imported")
    from api_agents.api_gateway.routers.alerts import router as alerts_router
    print("[OK] Alerts Router imported")
    from api_agents.api_gateway.routers.agents import router as agents_router
    print("[OK] Agents Router imported")
    from api_agents.api_gateway.routers.llm import router as llm_router
    print("[OK] LLM Router imported")
    from api_agents.api_gateway.routers.system import router as system_router
    print("[OK] System Router imported")
    from api_agents.api_gateway.routers.metrics import router as metrics_router
    print("[OK] Metrics Router imported")
    from api_agents.api_gateway.routers.emails import router as emails_router
    print("[OK] Emails Router imported")
    from api_agents.api_gateway.routers.connection import router as connection_router
    print("[OK] Connection Router imported")
    from api_agents.api_gateway.routers.tasks import router as tasks_router
    print("[OK] Tasks Router imported")
    from api_agents.api_gateway.routers.workflows import router as workflows_router
    print("[OK] Workflows Router imported")
    from api_agents.api_gateway.routers.auth import router as auth_router
    print("[OK] Auth Router imported")
    from api_agents.api_gateway.routers.oem import router as oem_router
    print("[OK] OEM Router imported")

except Exception as e:
    print(f"[ERROR] IMPORT ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="M-DN AI CMDB",
    version="3.2.0",
    description="AI-Powered Database Management - With Authentication",
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
app.include_router(auth_router, prefix="/api", tags=["Authentication"])
app.include_router(oem_router, prefix="/api", tags=["OEM"])

# =============================================================================
# Startup Event
# =============================================================================

@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("🚀 M-DN AI CMDB v3.2.0 - With Authentication")
    print(f"📁 Routers loaded: inventory, alerts, agents, llm, system, metrics, emails, connection, tasks, workflows, auth")
    print(f"🌐 CORS Origins: {ALLOWED_ORIGINS}")
    print("🔒 Authentication enabled")
    
    try:
        # Ensure default admin user exists
        from .services.auth_service import get_auth_service
        auth_service = get_auth_service()
        await auth_service.ensure_admin_exists()
    except Exception as e:
        print(f"❌ Startup Error - Failed to initialize Auth Service: {e}")
        print("   The application will continue, but authentication might not work.")
    
    print("=" * 60)

# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    import uvicorn
    
    port = int(os.getenv("BACKEND_PORT", 8000))
    print(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
