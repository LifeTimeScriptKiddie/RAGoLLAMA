# ollama_embed.py
import requests
from langchain.embeddings.base import Embeddings
from typing import List
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

class OllamaEmbeddings(Embeddings):
    def __init__(self, model: str = "nomic-embed-text", endpoint: str = None):
        self.model = model
        self.endpoint = endpoint or os.getenv("OLLAMA_EMBEDDING_URL", "http://localhost:11434/api/embeddings")
        self.headers = {"Content-Type": "application/json"}

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        logging.info(f"Embedding {len(texts)} documents with Ollama model: {self.model}")
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        try:
            response = requests.post(
                self.endpoint,
                json={"model": self.model, "prompt": text},
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except requests.RequestException as e:
            logging.error(f"Error calling Ollama embeddings API: {e}")
            return []