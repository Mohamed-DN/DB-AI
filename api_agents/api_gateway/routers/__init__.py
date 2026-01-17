"""
API Gateway Routers Package
"""
from .inventory import router as inventory_router
from .alerts import router as alerts_router
from .agents import router as agents_router
from .llm import router as llm_router
from .system import router as system_router
from .metrics import router as metrics_router
from .emails import router as emails_router
from .connection import router as connection_router

__all__ = [
    "inventory_router",
    "alerts_router",
    "agents_router",
    "llm_router",
    "system_router",
    "metrics_router",
    "emails_router",
    "connection_router"
]
