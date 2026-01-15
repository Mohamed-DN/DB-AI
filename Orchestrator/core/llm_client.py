"""
LLM Client for communicating with Ollama
"""
import os
import requests
import json
from typing import Dict, Optional

class LLMClient:
    """Client for Ollama LLM"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3:8b"):
        self.base_url = base_url
        self.model = model

    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """Generate response from LLM"""
        
        url = f"{self.base_url}/api/generate"
        
        full_prompt = prompt
        if system_prompt:
             # Basic formatting for Llama 3 - though API handles raw prompts too
            full_prompt = f"System: {system_prompt}\nUser: {prompt}\nAssistant:"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            print(f"❌ Error communicating with LLM: {e}")
            return "Error generating response."

    def analyze_alert(self, alert: Dict) -> Dict:
        """Analyze an alert and decide on action"""
        
        system_prompt = """You are the AI Brain of the Nexi CMDB system. 
        Your job is to analyze database alerts and decide on the appropriate response.
        If a database is DOWN, you MUST draft a high-priority email to the DBA team.
        Return your response in JSON format with fields: 'severity', 'action', 'email_subject', 'email_body'."""
        
        prompt = f"""Analyze this alert:
        Host: {alert.get('host_name')}
        Service: {alert.get('service')}
        State: {alert.get('state')}
        Message: {alert.get('output')}
        
        Determine the severity and draft an email to Mohamed (the DBA)."""
        
        response_text = self.generate_response(prompt, system_prompt)
        
        # Try to parse JSON from LLM response (simple heuristic if it wraps in code blocks)
        try:
            # Strip markdown code blocks if present
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            # Find the first { and last }
            start = clean_text.find("{")
            end = clean_text.rfind("}") + 1
            if start != -1 and end != -1:
                return json.loads(clean_text[start:end])
            else:
                return {"action": "LOG_ONLY", "reason": "Could not parse JSON", "raw_response": response_text}
        except Exception:
            # Fallback
            return {
                "action": "EMAIL_REQUIRED" if "DOWN" in str(alert) else "LOG", 
                "email_body": response_text
            }
