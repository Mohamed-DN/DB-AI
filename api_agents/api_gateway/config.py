"""
API Gateway Configuration
Centralizes environment loading, Langfuse initialization, and constants.
"""
import os
from dotenv import load_dotenv

# Load environment - prioritize .env.v2 for V2 Shadow Mode
env_v2_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env.v2'))
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env'))

if os.path.exists(env_v2_path):
    print(f"[CONFIG] Loading from {env_v2_path}")
    load_dotenv(env_v2_path, override=True)
elif os.path.exists(env_path):
    print(f"[CONFIG] Loading from {os.path.abspath(env_path)}")
    load_dotenv(env_path)
else:
    print("[CONFIG] Warning: No .env file found")

# =============================================================================
# CORS Configuration
# =============================================================================
ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS", 
    "http://localhost:4002,http://localhost:5173,http://127.0.0.1:4002,http://localhost:3002"
).split(",")

# =============================================================================
# LLM Configuration
# =============================================================================
from llm.config.llm_config import (
    LLM_MODELS, DEFAULT_MODEL, FALLBACK_MODEL, OLLAMA_CONFIG,
    get_model_info, get_recommended_models, get_all_models
)

# Current model state (mutable)
current_llm_model = DEFAULT_MODEL

# =============================================================================
# Langfuse LLM Observability
# =============================================================================
LANGFUSE_ENABLED = False
langfuse = None

try:
    from langfuse import Langfuse
    LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://localhost:3001")
    LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
    
    if LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY:
        langfuse = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST
        )
        LANGFUSE_ENABLED = True
        print("[CONFIG] Langfuse observability enabled")
    else:
        print("[CONFIG] Langfuse keys not set, observability disabled")
except ImportError:
    print("[CONFIG] Langfuse not installed, observability disabled")

# =============================================================================
# Agent Configuration
# =============================================================================
AGENTS_STATE = {
    "scout": {"running": False, "process": None},
    "collector": {"running": False, "process": None},
    "watcher": {"running": False, "process": None},
    "criticalalert": {"running": False, "process": None},
    "forensicanalyzer": {"running": False, "process": None},
    "checkmk_bridge": {"running": False, "process": None},
    "enricher": {"running": False, "process": None},
    "discovery": {"running": False, "process": None},
    "userprovisioner": {"running": False, "process": None},
    "ingestion": {"running": False, "process": None}
}

AGENT_SCRIPTS = {
    "scout": "../workers/Scout/scout_agent.py",
    "collector": "../workers/Collector/collector_agent.py",
    "watcher": "../workers/Watcher/watcher_agent.py",
    "criticalalert": "../workers/CriticalAlert/critical_alert_agent.py",
    "forensicanalyzer": "../workers/Watcher/ai_analyzer.py",
    "checkmk_bridge": "../workers/CheckMK_Bridge/main.py",
    "enricher": "../workers/Enricher/enricher_agent.py",
    "discovery": "../workers/Discovery/discovery_agent.py",
    "userprovisioner": "../workers/UserProvisioner/user_provisioner_agent.py",
    "ingestion": "../workers/Ingestion/ingestion_worker.py"
}
