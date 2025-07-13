import requests
import json
import os
import time
from typing import List, Dict, Any

class OllamaClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")
        self.available_models = []
        self.default_model = None
        self._check_connection()
    
    def test_connection(self) -> bool:
        """Test if Ollama is reachable"""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False
    
    def _check_connection(self):
        """Check Ollama connection and get available models"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # First test basic connectivity
                if not self.test_connection():
                    if attempt < max_retries - 1:
                        print(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        print(f"Warning: Cannot reach Ollama at {self.base_url} after {max_retries} attempts")
                        print("The system will work with limited functionality without LLM responses.")
                        return
                    
                self.available_models = self.list_models()
                if self.available_models:
                    # Prefer specific models in order (updated for our optimized models)
                    preferred_models = [
                        "llama3.2:1b",           # Our recommended default (1.3GB)
                        "codegemma:2b",          # Good for coding tasks (1.6GB)
                        "phi3:latest",           # Most capable (2.2GB)
                        "tinyllama:latest",      # Fastest (637MB)
                        "qwen2.5:0.5b",          # Ultra-fast (397MB)
                        "llama3.2:latest", "llama3.2", 
                        "phi3", "codegemma:latest",
                        "tinyllama", "qwen:latest", "qwen",
                        "gemma:latest", "gemma", "mistral:latest", "mistral"
                    ]
                    
                    for preferred in preferred_models:
                        if preferred in self.available_models:
                            self.default_model = preferred
                            print(f"Selected preferred model: {preferred}")
                            break
                    
                    # If no preferred model found, use the first available
                    if not self.default_model and self.available_models:
                        self.default_model = self.available_models[0]
                        
                    print(f"Ollama connected. Available models: {self.available_models}")
                    print(f"Default model set to: {self.default_model}")
                    return  # Success, exit retry loop
                else:
                    if attempt < max_retries - 1:
                        print(f"No models found on attempt {attempt + 1}, retrying...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        print("Ollama connected but no models found after all attempts. You may need to pull models first.")
                        return
                        
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed: {str(e)}, retrying...")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"Warning: Could not connect to Ollama after {max_retries} attempts: {str(e)}")
                    print("The system will work with limited functionality without LLM responses.")
                    return
    
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
                timeout=120  # Increased timeout for generation
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
                timeout=120  # Increased timeout for chat
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
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
            return []
        except Exception as e:
            print(f"Error listing models: {str(e)}")
            return []

# Global client instance
ollama_client = OllamaClient()