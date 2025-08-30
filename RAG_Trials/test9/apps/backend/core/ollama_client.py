import httpx
import json
from typing import Dict, Any, List, Optional, AsyncGenerator
from .settings import settings
import asyncio

class OllamaClient:
    """Async client for Ollama API."""
    
    def __init__(self, host: str = None, port: int = None):
        self.host = host or settings.ollama_host
        self.port = port or settings.ollama_port
        self.base_url = f"http://{self.host}:{self.port}"
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def health_check(self) -> bool:
        """Check if Ollama is healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except Exception as e:
            raise Exception(f"Failed to list models: {e}")
    
    async def pull_model(self, model: str) -> bool:
        """Pull a model if not available."""
        try:
            # Check if model exists
            models = await self.list_models()
            model_names = [m.get("name", "") for m in models]
            
            if model in model_names:
                return True
            
            # Pull model
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": model}
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            print(f"Failed to pull model {model}: {e}")
            return False
    
    async def generate(
        self, 
        model: str, 
        prompt: str, 
        context: Optional[List[str]] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate response from model."""
        
        # Ensure model is available
        await self.pull_model(model)
        
        # Build prompt with context
        full_prompt = prompt
        if context:
            context_text = "\n\n".join(context)
            full_prompt = f"""Context information:
{context_text}

Question: {prompt}

Answer based on the context above:"""
        
        try:
            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120.0
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {
                "response": result.get("response", ""),
                "model": model,
                "total_duration": result.get("total_duration", 0),
                "load_duration": result.get("load_duration", 0),
                "prompt_eval_count": result.get("prompt_eval_count", 0),
                "eval_count": result.get("eval_count", 0),
                "context": result.get("context", [])
            }
            
        except httpx.TimeoutException:
            raise Exception("Ollama request timed out")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Ollama API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Ollama generation failed: {e}")
    
    async def generate_stream(
        self,
        model: str,
        prompt: str,
        context: Optional[List[str]] = None,
        temperature: float = 0.1
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from model."""
        
        await self.pull_model(model)
        
        # Build prompt with context
        full_prompt = prompt
        if context:
            context_text = "\n\n".join(context)
            full_prompt = f"""Context information:
{context_text}

Question: {prompt}

Answer based on the context above:"""
        
        try:
            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": True,
                "options": {
                    "temperature": temperature,
                }
            }
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120.0
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            raise Exception(f"Ollama streaming failed: {e}")
    
    async def embed(self, model: str, text: str) -> List[float]:
        """Generate embeddings using Ollama."""
        try:
            await self.pull_model(model)
            
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("embedding", [])
            
        except Exception as e:
            raise Exception(f"Ollama embedding failed: {e}")

# Singleton instance
_ollama_client = None

async def get_ollama_client() -> OllamaClient:
    """Get Ollama client instance."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client