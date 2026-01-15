"""
__init__.py for Orchestrator config module
"""
from .llm_config import (
    LLM_MODELS,
    DEFAULT_MODEL,
    FALLBACK_MODEL,
    OLLAMA_CONFIG,
    get_model_info,
    get_recommended_models,
    get_all_models
)
