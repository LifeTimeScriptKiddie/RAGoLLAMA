#!/usr/bin/env python3
"""
RAG-Ollama CLI Management Tool

Provides command-line interface for managing the RAG system:
- Document ingestion
- Index management
- System status
- User management
- Evaluation
"""

import argparse
import asyncio
import json
import sys
import requests
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class RAGClient:
    """Client for RAG API."""
    
    def __init__(self, base_url: str = "http://localhost:8000", token: str = None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def login(self, username: str, password: str) -> str:
        """Login and get access token."""
        response = self.session.post(
            f"{self.base_url}/auth/login",
            data={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            self.token = token_data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return self.token
        else:
            raise Exception(f"Login failed: {response.text}")
    
    def upload_document(self, file_path: str) -> Dict[str, Any]:
        """Upload document for processing."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'rb') as f:
            files = {"file": (file_path.name, f, "application/octet-stream")}
            response = self.session.post(f"{self.base_url}/upload/document", files=files)
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    
    def query(self, question: str, k: int = 5) -> Dict[str, Any]:
        """Query the RAG system."""
        response = self.session.post(
            f"{self.base_url}/query/",
            json={"query": question, "k": k}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    
    def get_index_info(self) -> Dict[str, Any]:
        """Get index information."""
        response = self.session.get(f"{self.base_url}/admin/index/info")
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    
    def list_models(self) -> Dict[str, Any]:
        """List available Ollama models."""
        response = self.session.get(f"{self.base_url}/admin/models")
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    
    def health_check(self) -> Dict[str, Any]:
        """Check system health."""
        response = self.session.get(f"{self.base_url}/admin/health")
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

def cmd_login(args):
    """Login command."""
    client = RAGClient(args.url)
    
    try:
        token = client.login(args.username, args.password)
        print(f"✅ Login successful!")
        print(f"Access token: {token}")
        
        # Save token to file for later use
        token_file = Path.home() / ".rag_token"
        with open(token_file, 'w') as f:
            f.write(token)
        
        print(f"Token saved to: {token_file}")
        
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return 1
    
    return 0

def cmd_upload(args):
    """Upload document command."""
    token = load_token()
    client = RAGClient(args.url, token)
    
    try:
        print(f"Uploading document: {args.file}")
        result = client.upload_document(args.file)
        
        print("✅ Upload successful!")
        print(json.dumps(result, indent=2))
        
        if args.wait:
            print("Waiting for processing to complete...")
            # TODO: Poll status until completed
            
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return 1
    
    return 0

def cmd_query(args):
    """Query command."""
    token = load_token()
    client = RAGClient(args.url, token)
    
    try:
        print(f"Querying: {args.question}")
        result = client.query(args.question, args.k)
        
        print("\n📖 Answer:")
        print(result["answer"])
        
        if result["sources"]:
            print(f"\n🔍 Sources ({len(result['sources'])}):")
            for i, source in enumerate(result["sources"], 1):
                print(f"{i}. Score: {source.get('score', 'N/A'):.3f}")
                if 'metadata' in source:
                    meta = source['metadata']
                    print(f"   Doc: {meta.get('doc_id', 'N/A')}")
                    print(f"   Chunk: {source.get('chunk_id', 'N/A')}")
        
        print(f"\n⏱️  Latency: {result['latency_ms']:.0f}ms")
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return 1
    
    return 0

def cmd_status(args):
    """System status command."""
    token = load_token() if args.detailed else None
    client = RAGClient(args.url, token)
    
    try:
        # Health check (public)
        health = client.health_check()
        print("🏥 System Health:")
        print(f"  Status: {health.get('status', 'unknown')}")
        
        if args.detailed and token:
            # Detailed info (requires auth)
            index_info = client.get_index_info()
            models = client.list_models()
            
            print("\n📊 Index Information:")
            if "vector_store" in index_info:
                vs = index_info["vector_store"]
                print(f"  Total vectors: {vs.get('total_vectors', 0)}")
                print(f"  Index version: {vs.get('current_version', 'N/A')}")
                print(f"  Dimension: {vs.get('dimension', 0)}")
            
            if "ingestion_ledger" in index_info:
                ledger = index_info["ingestion_ledger"]
                print(f"  Total documents: {ledger.get('total_documents', 0)}")
                print(f"  Total chunks: {ledger.get('total_chunks', 0)}")
            
            print("\n🤖 Available Models:")
            for model in models.get("models", []):
                print(f"  - {model.get('name', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return 1
    
    return 0

def cmd_eval(args):
    """Run evaluation command."""
    from apps.rag.evals.run_eval import RAGEvaluator
    
    async def run_evaluation():
        try:
            evaluator = RAGEvaluator()
            results = await evaluator.run_evaluation()
            
            evaluator.print_results(results)
            
            if args.save:
                evaluator.save_results(results, args.save)
            
            # Return exit code based on performance
            hit_rate = results["summary"]["avg_hit_rate"]
            return 0 if hit_rate >= 0.5 else 1
            
        except Exception as e:
            print(f"❌ Evaluation failed: {e}")
            return 1
    
    return asyncio.run(run_evaluation())

def load_token() -> str:
    """Load saved access token."""
    token_file = Path.home() / ".rag_token"
    
    if token_file.exists():
        with open(token_file, 'r') as f:
            return f.read().strip()
    
    return None

def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(description="RAG-Ollama CLI Management Tool")
    parser.add_argument("--url", default="http://localhost:8000", help="Backend URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Login command
    login_parser = subparsers.add_parser("login", help="Login to get access token")
    login_parser.add_argument("username", help="Username")
    login_parser.add_argument("password", help="Password")
    
    # Upload command  
    upload_parser = subparsers.add_parser("upload", help="Upload document")
    upload_parser.add_argument("file", help="File to upload")
    upload_parser.add_argument("--wait", action="store_true", help="Wait for processing")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query documents")
    query_parser.add_argument("question", help="Question to ask")
    query_parser.add_argument("--k", type=int, default=5, help="Number of results")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.add_argument("--detailed", action="store_true", help="Show detailed info")
    
    # Evaluation command
    eval_parser = subparsers.add_parser("eval", help="Run evaluation")
    eval_parser.add_argument("--save", help="Save results to file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Command dispatch
    commands = {
        "login": cmd_login,
        "upload": cmd_upload,
        "query": cmd_query,
        "status": cmd_status,
        "eval": cmd_eval,
    }
    
    if args.command in commands:
        try:
            return commands[args.command](args)
        except KeyboardInterrupt:
            print("\n⛔ Interrupted by user")
            return 1
    else:
        print(f"Unknown command: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())