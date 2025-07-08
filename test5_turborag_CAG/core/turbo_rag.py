import numpy as np
from typing import List, Tuple, Dict, Any
from sentence_transformers import SentenceTransformer
from .vector_store import query as vector_query
from .ollama_client import ollama_client
import json
import os

class TurboRAG:
    def __init__(self, model_name: str = None):
        # Use best available model instead of hardcoded one
        self.requested_model = model_name or "llama3.2:latest"
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
    def retrieve_and_rank(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        """Enhanced retrieval with re-ranking"""
        # Get initial results from vector store
        initial_results = vector_query(query, k=k*2)  # Get more candidates
        
        if not initial_results:
            return []
        
        # Re-rank based on query similarity
        query_embedding = self.embedding_model.encode([query])
        reranked_results = []
        
        for text, original_score in initial_results:
            # Calculate semantic similarity
            text_embedding = self.embedding_model.encode([text])
            similarity = np.dot(query_embedding[0], text_embedding[0]) / (
                np.linalg.norm(query_embedding[0]) * np.linalg.norm(text_embedding[0])
            )
            
            # Combine original distance with semantic similarity
            combined_score = (1 - original_score) * 0.7 + similarity * 0.3
            reranked_results.append((text, combined_score))
        
        # Sort by combined score and return top k
        reranked_results.sort(key=lambda x: x[1], reverse=True)
        return reranked_results[:k]
    
    def generate_answer(self, query: str, context_docs: List[str]) -> str:
        """Generate answer using retrieved context"""
        context = "\n\n".join([f"Document {i+1}: {doc}" for i, doc in enumerate(context_docs)])
        
        prompt = f"""Based on the following context documents, answer the question. If the answer is not in the context, say so clearly.

Context:
{context}

Question: {query}

Answer:"""
        
        return ollama_client.generate(self.requested_model, prompt)
    
    def query(self, question: str, k: int = 3) -> Dict[str, Any]:
        """Complete RAG pipeline"""
        # Retrieve relevant documents
        retrieved_docs = self.retrieve_and_rank(question, k)
        
        if not retrieved_docs:
            return {
                "answer": "No relevant documents found.",
                "sources": [],
                "confidence": 0.0
            }
        
        # Extract text and scores
        doc_texts = [doc[0] for doc in retrieved_docs]
        doc_scores = [doc[1] for doc in retrieved_docs]
        
        # Generate answer
        answer = self.generate_answer(question, doc_texts)
        
        # Calculate confidence based on retrieval scores
        avg_confidence = sum(doc_scores) / len(doc_scores) if doc_scores else 0.0
        
        return {
            "answer": answer,
            "sources": [{"text": text[:200] + "...", "score": score} 
                       for text, score in retrieved_docs],
            "confidence": avg_confidence
        }

# Global instance
turbo_rag = TurboRAG()