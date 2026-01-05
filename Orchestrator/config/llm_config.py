"""
LLM Configuration for Nexi DBA AI
Optimized for RTX 5070 Ti (16GB VRAM)
"""

# Available models optimized for 16GB VRAM
LLM_MODELS = {
    # Primary - Best balance of performance and quality
    "qwen2.5:14b": {
        "name": "Qwen 2.5 14B",
        "vram_gb": 12,
        "description": "Ottimo per italiano, reasoning avanzato",
        "use_case": "chat",
        "recommended": True
    },
    
    # Coding - Specialized for SQL and scripts
    "codellama:13b": {
        "name": "CodeLlama 13B",
        "vram_gb": 11,
        "description": "SQL generation, script development",
        "use_case": "coding",
        "recommended": True
    },
    
    # Reasoning - Deep analysis
    "deepseek-r1:14b": {
        "name": "DeepSeek R1 14B",
        "vram_gb": 12,
        "description": "Analisi complesse, troubleshooting",
        "use_case": "reasoning",
        "recommended": False
    },
    
    # Lightweight - Fast responses
    "llama3:8b": {
        "name": "Llama 3 8B",
        "vram_gb": 7,
        "description": "Risposte rapide, basso consumo",
        "use_case": "fast",
        "recommended": False
    },
    
    # Max Performance - Full GPU utilization
    "llama3.1:70b-q4_K_M": {
        "name": "Llama 3.1 70B (Quantized)",
        "vram_gb": 15,
        "description": "Massime prestazioni, richiede tutta la VRAM",
        "use_case": "max",
        "recommended": False
    }
}

# Default model for new installations
DEFAULT_MODEL = "qwen2.5:14b"

# Fallback if primary fails
FALLBACK_MODEL = "llama3:8b"

# Ollama configuration
OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
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
