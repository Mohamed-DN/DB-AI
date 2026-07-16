"""
Ollama LLM Client - Interface to Local LLM
Connects to Ollama running in Docker at m-dn-ollama:11434
"""

import os
import json
import requests
from typing import Optional, Dict, List, Any

class OllamaClient:
    """Client for interacting with Ollama LLM API"""
    
    def __init__(self, host: str = None, model: str = None):
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.timeout = 120  # seconds
        
    def generate(self, prompt: str, system: str = None, context: List[int] = None) -> Dict[str, Any]:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            system: Optional system prompt for role setting
            context: Optional context from previous conversation
            
        Returns:
            Dict with 'response', 'context', and metadata
        """
        url = f"{self.host}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if system:
            payload["system"] = system
        if context:
            payload["context"] = context
            
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to Ollama. Is it running?", "response": None}
        except requests.exceptions.Timeout:
            return {"error": "Request timed out", "response": None}
        except Exception as e:
            return {"error": str(e), "response": None}
    
    def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Chat completion API (multi-turn conversation).
        
        Args:
            messages: List of {"role": "user|assistant|system", "content": "..."}
            
        Returns:
            Response dict with 'message' containing assistant reply
        """
        url = f"{self.host}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "message": None}
    
    def analyze_db_error(self, error_line: str, context_lines: List[str]) -> str:
        """
        Specialized method for analyzing database errors with context.
        
        Args:
            error_line: The specific error line (e.g., ORA-00600)
            context_lines: List of preceding log lines for context
            
        Returns:
            AI analysis as string
        """
        system_prompt = """You are an expert Oracle DBA and Database Reliability Engineer. 
Your task is to analyze database errors and provide:
1. Error Classification (Severity: Critical/High/Medium/Low)
2. Root Cause Hypothesis
3. Immediate Actions Required
4. Long-term Remediation

Be concise but thorough. Reference specific Oracle documentation when relevant."""

        context_text = "\n".join(context_lines[-50:])  # Last 50 lines for context
        
        user_prompt = f"""Analyze this database error:

**Error Line:**
{error_line}

**Preceding Log Context (last 50 lines):**
```
{context_text}
```

Provide your analysis:"""

        result = self.generate(user_prompt, system=system_prompt)
        
        if result.get("error"):
            return f"AI Analysis Failed: {result['error']}"
        
        return result.get("response", "No response generated")
    
    def list_models(self) -> List[str]:
        """Get list of available models"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except:
            return []
    
    def health_check(self) -> bool:
        """Check if Ollama is reachable"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


# Quick test
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    client = OllamaClient()
    
    print("🤖 Testing Ollama Connection...")
    if client.health_check():
        print("✅ Ollama is reachable")
        print(f"   Available models: {client.list_models()}")
        
        # Quick test
        print("\n📝 Testing generation...")
        result = client.generate("What is Oracle ORA-00600 error? One sentence only.")
        if result.get("response"):
            print(f"   Response: {result['response'][:200]}...")
        else:
            print(f"   Error: {result.get('error')}")
    else:
        print("❌ Cannot connect to Ollama")
