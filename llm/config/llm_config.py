"""
LLM Configuration for M-DN DBA AI
Optimized for RTX 5070 Ti (16GB VRAM)
"""
import os

# Available models optimized for 16GB VRAM
LLM_MODELS = {
    "deepseek-r1:8b": {
        "name": "DeepSeek R1 8B",
        "vram_gb": 8,
        "description": "DeepSeek Reasoning Model (Installed)",
        "use_case": "reasoning",
        "recommended": True
    },
    # Primary - Best all-rounder for 16GB VRAM
    "qwen2.5:14b": {
        "name": "Qwen 2.5 14B",
        "vram_gb": 12,
        "description": "Balanced speed and quality. Strong in Italian.",
        "use_case": "chat",
        "recommended": True
    },
    
    # Coding/Reasoning - The "Thinking" Model
    "deepseek-coder-v2:16b": {
        "name": "DeepSeek Coder V2 16B",
        "vram_gb": 14,
        "description": "Advanced reasoning model. Strong for code and complex logic.",
        "use_case": "reasoning",
        "recommended": True
    },
    
    # Pure Coding Alternative
    "qwen2.5-coder:14b": {
        "name": "Qwen 2.5 Coder 14B",
        "vram_gb": 12,
        "description": "Specialized in code and SQL generation.",
        "use_case": "coding",
        "recommended": False
    },
    
    # Lightweight - Fast responses
    "llama3.1:8b": {
        "name": "Llama 3.1 8B",
        "vram_gb": 7,
        "description": "Fast responses, low resource usage.",
        "use_case": "fast",
        "recommended": False
    }
}

# Default model for new installations
DEFAULT_MODEL = "deepseek-r1:8b"

# Fallback if primary fails
FALLBACK_MODEL = "llama3.1:8b"

# Ollama configuration
OLLAMA_CONFIG = {
    "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
    "timeout": 120,  # seconds
    "stream": True,  # Enable streaming for better UX
    "options": {
        "num_gpu": 99,  # Use all GPU layers
        "num_ctx": 8192,  # Context window
        "temperature": 0.7,
        "top_p": 0.9
    }
}

def get_model_info(model_id: str) -> dict:
    """Get model information by ID"""
    return LLM_MODELS.get(model_id, LLM_MODELS[DEFAULT_MODEL])

def get_recommended_models() -> list:
    """Get list of recommended models"""
    return [k for k, v in LLM_MODELS.items() if v.get("recommended")]

def get_all_models() -> list:
    """Get all available models"""
    return list(LLM_MODELS.keys())
