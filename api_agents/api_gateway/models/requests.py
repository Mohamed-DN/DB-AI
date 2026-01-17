"""
Pydantic Request/Response Models for API Gateway
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# =============================================================================
# LLM Models
# =============================================================================
class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = None  # Override current model


class ModelSwitchRequest(BaseModel):
    model: str


# =============================================================================
# System Models
# =============================================================================
class SystemStatusRequest(BaseModel):
    status: str  # RUNNING or PAUSED


class ConfigUpdateRequest(BaseModel):
    scout_interval: Optional[int] = None
    criticalalert_interval: Optional[int] = None
    watcher_interval: Optional[int] = None
    forensicanalyzer_interval: Optional[int] = None
    checkmk_bridge_interval: Optional[int] = None
    collector_interval: Optional[int] = None
