"""
Ollama Client

Handles communication with Ollama service for LLM inference
and provides RAG-based question answering capabilities.
"""

import requests
import json
import logging
from typing import List, Dict, Any, Optional, Generator
import time

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama LLM service."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Ollama client.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.base_url = config.get("ollama_url", "http://localhost:11434")
        self.default_model = config.get("default_model", "llama2")
        self.timeout = config.get("timeout", 30)
        self.max_retries = config.get("max_retries", 3)
        
        # Validate connection
        self._check_connection()
    
    def _check_connection(self):
        """Check if Ollama service is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            if response.status_code == 200:
                logger.info("Ollama service is available")
                available_models = [model["name"] for model in response.json().get("models", [])]
                logger.info(f"Available models: {available_models}")
            else:
                logger.warning(f"Ollama service responded with status {response.status_code}")
        except Exception as e:
            logger.warning(f"Cannot connect to Ollama service: {e}")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models in Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            response.raise_for_status()
            
            return response.json().get("models", [])
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=300  # Longer timeout for model pulling
            )
            response.raise_for_status()
            
            logger.info(f"Successfully pulled model {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False
    
    def generate(self, prompt: str, model: Optional[str] = None, 
                 system_prompt: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: Optional[int] = None) -> str:
        """
        Generate text using Ollama.
        
        Args:
            prompt: Input prompt
            model: Model name (uses default if None)
            system_prompt: System prompt for context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("response", "")
                
            except Exception as e:
                logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All generation attempts failed for model {model}")
                    raise
    
    def generate_stream(self, prompt: str, model: Optional[str] = None,
                       system_prompt: Optional[str] = None,
                       temperature: float = 0.7) -> Generator[str, None, None]:
        """
        Generate text using Ollama with streaming.
        
        Args:
            prompt: Input prompt
            model: Model name (uses default if None)
            system_prompt: System prompt for context
            temperature: Sampling temperature
            
        Yields:
            Generated text chunks
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    if chunk.get("response"):
                        yield chunk["response"]
                    if chunk.get("done", False):
                        break
                        
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise
    
    def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None,
             temperature: float = 0.7) -> str:
        """
        Chat with Ollama using conversation format.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            model: Model name (uses default if None)
            temperature: Sampling temperature
            
        Returns:
            Assistant response
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("message", {}).get("content", "")
                
            except Exception as e:
                logger.warning(f"Chat attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"All chat attempts failed for model {model}")
                    raise
    
    def rag_query(self, question: str, context_chunks: List[str],
                  model: Optional[str] = None,
                  max_context_length: int = 4000) -> Dict[str, Any]:
        """
        Perform RAG-based question answering.
        
        Args:
            question: User question
            context_chunks: Retrieved document chunks
            model: Model name (uses default if None)
            max_context_length: Maximum context length
            
        Returns:
            Dictionary with answer and metadata
        """
        model = model or self.default_model
        
        # Truncate context if too long
        context = "\n\n".join(context_chunks)
        if len(context) > max_context_length:
            context = context[:max_context_length] + "..."
        
        system_prompt = """You are a helpful assistant that answers questions based on the provided context. 
Use only the information given in the context to answer questions. 
If the answer cannot be found in the context, say so clearly.
Be concise and accurate in your responses."""
        
        user_prompt = f"""Context:
{context}

Question: {question}

Answer:"""
        
        try:
            start_time = time.time()
            
            answer = self.generate(
                prompt=user_prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=0.3  # Lower temperature for factual responses
            )
            
            generation_time = time.time() - start_time
            
            return {
                "answer": answer,
                "model": model,
                "context_chunks_used": len(context_chunks),
                "context_length": len(context),
                "generation_time": generation_time,
                "question": question
            }
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return {
                "answer": f"Error generating answer: {str(e)}",
                "model": model,
                "context_chunks_used": 0,
                "context_length": 0,
                "generation_time": 0,
                "question": question,
                "error": str(e)
            }
    
    def compare_rag_methods(self, question: str, 
                           docling_chunks: List[str],
                           microsoft_chunks: List[str],
                           model: Optional[str] = None) -> Dict[str, Any]:
        """
        Compare RAG responses using different embedding methods.
        
        Args:
            question: User question
            docling_chunks: Chunks retrieved using Docling embeddings
            microsoft_chunks: Chunks retrieved using Microsoft embeddings
            model: Model name (uses default if None)
            
        Returns:
            Comparison results
        """
        # Get answers using both chunk sets
        docling_result = self.rag_query(question, docling_chunks, model)
        microsoft_result = self.rag_query(question, microsoft_chunks, model)
        
        # Calculate similarity metrics
        docling_answer = docling_result["answer"]
        microsoft_answer = microsoft_result["answer"]
        
        # Simple text similarity (could be enhanced with embeddings)
        answer_similarity = self._calculate_text_similarity(docling_answer, microsoft_answer)
        
        return {
            "question": question,
            "docling_result": docling_result,
            "microsoft_result": microsoft_result,
            "answer_similarity": answer_similarity,
            "context_overlap": self._calculate_context_overlap(docling_chunks, microsoft_chunks),
            "recommendation": self._recommend_method(docling_result, microsoft_result),
            "model": model or self.default_model
        }
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity between two strings."""
        if not text1 or not text2:
            return 0.0
        
        # Convert to sets of words for Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_context_overlap(self, chunks1: List[str], chunks2: List[str]) -> float:
        """Calculate overlap between two sets of context chunks."""
        if not chunks1 or not chunks2:
            return 0.0
        
        # Convert chunks to sets for comparison
        set1 = set(chunks1)
        set2 = set(chunks2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _recommend_method(self, docling_result: Dict[str, Any], 
                         microsoft_result: Dict[str, Any]) -> str:
        """Recommend which method performed better."""
        # Simple heuristic based on generation time and answer length
        docling_score = 0
        microsoft_score = 0
        
        # Prefer faster generation
        if docling_result["generation_time"] < microsoft_result["generation_time"]:
            docling_score += 1
        else:
            microsoft_score += 1
        
        # Prefer more detailed answers (within reason)
        docling_len = len(docling_result["answer"])
        microsoft_len = len(microsoft_result["answer"])
        
        if 50 <= docling_len <= 1000 and (microsoft_len < 50 or microsoft_len > 1000):
            docling_score += 1
        elif 50 <= microsoft_len <= 1000 and (docling_len < 50 or docling_len > 1000):
            microsoft_score += 1
        elif docling_len > microsoft_len:
            docling_score += 1
        else:
            microsoft_score += 1
        
        # Check for errors
        if "error" in docling_result:
            microsoft_score += 2
        if "error" in microsoft_result:
            docling_score += 2
        
        return "docling" if docling_score > microsoft_score else "microsoft"
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": model_name},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting model info for {model_name}: {e}")
            return {}