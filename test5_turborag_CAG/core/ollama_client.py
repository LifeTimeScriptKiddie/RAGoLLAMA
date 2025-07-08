import requests
import json
import os
from typing import List, Dict, Any

class OllamaClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")
        self.available_models = []
        self.default_model = None
        self._check_connection()
    
    def _check_connection(self):
        """Check Ollama connection and get available models"""
        try:
            self.available_models = self.list_models()
            if self.available_models:
                # Prefer specific models in order
                preferred_models = [
                    "llama3.2:latest", "llama3.2", "llama3.1:latest", "llama3.1", 
                    "llama3:latest", "llama3", "llama2:latest", "llama2",
                    "phi3:latest", "phi3", "gemma:latest", "gemma",
                    "qwen:latest", "qwen", "mistral:latest", "mistral"
                ]
                
                for preferred in preferred_models:
                    if preferred in self.available_models:
                        self.default_model = preferred
                        break
                
                # If no preferred model found, use the first available
                if not self.default_model and self.available_models:
                    self.default_model = self.available_models[0]
                    
                print(f"Ollama connected. Available models: {self.available_models}")
                print(f"Default model set to: {self.default_model}")
            else:
                print("Ollama connected but no models found. You may need to pull models first.")
        except Exception as e:
            print(f"Warning: Could not connect to Ollama: {str(e)}")
            print("The system will work with limited functionality without LLM responses.")
    
    def get_best_model(self, requested_model: str = None) -> str:
        """Get the best available model, with fallback logic"""
        if requested_model and requested_model in self.available_models:
            return requested_model
        elif self.default_model:
            return self.default_model
        elif self.available_models:
            return self.available_models[0]
        else:
            return None
    
    def is_available(self) -> bool:
        """Check if Ollama is available and has models"""
        return bool(self.available_models)
        
    def generate(self, model: str, prompt: str, context: List[str] = None) -> str:
        """Generate text using Ollama model"""
        # Check if Ollama is available
        if not self.is_available():
            return "⚠️ Ollama service is not available or no models are loaded. Please check your Ollama installation and pull some models."
        
        # Use best available model if requested model not found
        actual_model = self.get_best_model(model)
        if not actual_model:
            return "⚠️ No suitable models available. Please pull some models with 'ollama pull <model-name>'."
        
        try:
            payload = {
                "model": actual_model,
                "prompt": prompt,
                "stream": False
            }
            
            if context:
                payload["context"] = context
                
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json().get("response", "")
                if actual_model != model:
                    result = f"[Using {actual_model} instead of {model}]\n\n{result}"
                return result
            else:
                error_msg = f"Ollama API error: {response.status_code}"
                try:
                    error_detail = response.json().get("error", response.text)
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text}"
                return f"❌ {error_msg}"
                
        except requests.exceptions.RequestException as e:
            return f"❌ Connection error: {str(e)}. Make sure Ollama is running and accessible."
    
    def chat(self, model: str, messages: List[Dict[str, str]]) -> str:
        """Chat with Ollama model"""
        # Check if Ollama is available
        if not self.is_available():
            return "⚠️ Ollama service is not available or no models are loaded. Please check your Ollama installation and pull some models."
        
        # Use best available model if requested model not found
        actual_model = self.get_best_model(model)
        if not actual_model:
            return "⚠️ No suitable models available. Please pull some models with 'ollama pull <model-name>'."
        
        try:
            payload = {
                "model": actual_model,
                "messages": messages,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json().get("message", {}).get("content", "")
                if actual_model != model:
                    result = f"[Using {actual_model} instead of {model}]\n\n{result}"
                return result
            else:
                error_msg = f"Ollama API error: {response.status_code}"
                try:
                    error_detail = response.json().get("error", response.text)
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text}"
                return f"❌ {error_msg}"
                
        except requests.exceptions.RequestException as e:
            return f"❌ Connection error: {str(e)}. Make sure Ollama is running and accessible."
    
    def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
            return []
        except:
            return []

# Global client instance
ollama_client = OllamaClient()