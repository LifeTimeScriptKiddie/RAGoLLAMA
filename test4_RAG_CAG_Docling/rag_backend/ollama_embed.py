# ollama_embed.py
import requests
from langchain.embeddings.base import Embeddings
from typing import List

class OllamaEmbeddings(Embeddings):
    def __init__(self, model: str = "nomic-embed-text"):
        self.model = model
        self.endpoint = "http://localhost:11434/api/embeddings"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        response = requests.post(self.endpoint, json={
            "model": self.model,
            "prompt": text
        })
        return response.json()["embedding"]