import requests
import os
from typing import List, Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)

class BackendClient:
    """Client for communicating with the FastAPI backend"""
    
    def __init__(self):
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        self.session = requests.Session()
    
    def upload_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Upload a document to the backend"""
        try:
            files = {"file": (filename, file_content, "application/pdf")}
            response = self.session.post(
                f"{self.backend_url}/documents/upload",
                files=files,
                timeout=300  # 5 minutes for large files
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Document upload failed: {e}")
            raise Exception(f"Failed to upload document: {str(e)}")
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """Get list of all documents"""
        try:
            response = self.session.get(f"{self.backend_url}/documents")
            response.raise_for_status()
            return response.json()["documents"]
        except Exception as e:
            logging.error(f"Failed to list documents: {e}")
            return []
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document details"""
        try:
            response = self.session.get(f"{self.backend_url}/documents/{document_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Failed to get document: {e}")
            return None
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document"""
        try:
            response = self.session.delete(f"{self.backend_url}/documents/{document_id}")
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"Failed to delete document: {e}")
            return False
    
    def chat_with_document(
        self, 
        message: str, 
        document_id: str, 
        model: str = "llama3",
        top_k: int = 3
    ) -> str:
        """Chat with a specific document"""
        try:
            payload = {
                "message": message,
                "document_id": document_id,
                "model": model,
                "top_k": top_k
            }
            response = self.session.post(
                f"{self.backend_url}/chat/document",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            logging.error(f"Document chat failed: {e}")
            raise Exception(f"Chat failed: {str(e)}")
    
    def general_chat(self, message: str, model: str = "llama3") -> str:
        """General chat without document context"""
        try:
            payload = {
                "message": message,
                "model": model
            }
            response = self.session.post(
                f"{self.backend_url}/chat/general",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            logging.error(f"General chat failed: {e}")
            raise Exception(f"Chat failed: {str(e)}")
    
    def health_check(self) -> bool:
        """Check if backend is healthy"""
        try:
            response = self.session.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False