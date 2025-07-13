#!/usr/bin/env python3
"""
Import documents from our Financial Advisor knowledge base to Open WebUI's native knowledge base
"""

import requests
import json
import os
import time
from pathlib import Path

# Configuration
OPENWEBUI_URL = "http://localhost:3000"
KNOWLEDGE_API_URL = "http://localhost:8502"
DOCS_PATH = "/Users/tester/Documents/RAGoLLAMA/test5_turborag_CAG/docs"

def get_our_documents():
    """Get list of processed documents from our knowledge base"""
    try:
        response = requests.get(f"{KNOWLEDGE_API_URL}/documents")
        if response.status_code == 200:
            return response.json().get("documents", [])
        else:
            print(f"Error getting documents: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error connecting to knowledge base: {e}")
        return []

def upload_document_to_openwebui(file_path, auth_headers=None):
    """Upload a document to Open WebUI's knowledge base"""
    try:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False
            
        # Open WebUI file upload endpoint (this may need authentication)
        upload_url = f"{OPENWEBUI_URL}/api/v1/files/"
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            headers = auth_headers or {}
            
            response = requests.post(upload_url, files=files, headers=headers)
            
            if response.status_code in [200, 201]:
                print(f"✅ Uploaded: {os.path.basename(file_path)}")
                return True
            else:
                print(f"❌ Failed to upload {os.path.basename(file_path)}: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error uploading {file_path}: {e}")
        return False

def create_knowledge_base_in_openwebui():
    """Create a knowledge base in Open WebUI"""
    try:
        # This endpoint may require authentication
        kb_url = f"{OPENWEBUI_URL}/api/v1/knowledge/"
        
        kb_data = {
            "name": "Financial Advisor Documents",
            "description": "Cybersecurity, financial, and technical documents from the Financial Advisor Suite"
        }
        
        response = requests.post(kb_url, json=kb_data)
        
        if response.status_code in [200, 201]:
            print("✅ Knowledge base created in Open WebUI")
            return response.json().get("id")
        else:
            print(f"❌ Failed to create knowledge base: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating knowledge base: {e}")
        return None

def main():
    """Main import process"""
    print("🚀 Starting document import to Open WebUI...")
    
    # Step 1: Check our knowledge base status
    print("\n📊 Checking Financial Advisor Knowledge Base...")
    documents = get_our_documents()
    
    if not documents:
        print("❌ No documents found in Financial Advisor knowledge base")
        return
    
    print(f"✅ Found {len(documents)} documents in Financial Advisor knowledge base")
    
    # Step 2: List available documents
    print("\n📚 Available Documents:")
    successful_docs = [doc for doc in documents if doc['status'] == 'success']
    
    for doc in successful_docs[:10]:  # Show first 10
        print(f"   • {doc['filename']} ({doc['file_size']/1024/1024:.1f} MB)")
    
    if len(successful_docs) > 10:
        print(f"   ... and {len(successful_docs) - 10} more documents")
    
    # Step 3: Provide manual instructions (since Open WebUI APIs may need auth)
    print(f"\n🔧 Manual Import Instructions:")
    print(f"1. Open Open WebUI at {OPENWEBUI_URL}")
    print(f"2. Log in to your admin account")
    print(f"3. Go to 'Knowledge' or 'Documents' section")
    print(f"4. Create a new knowledge base called 'Financial Advisor Documents'")
    print(f"5. Upload documents from these folders:")
    print(f"   • {DOCS_PATH}/cyber/ (cybersecurity documents)")
    print(f"   • {DOCS_PATH}/financial/ (financial documents)")
    print(f"   • {DOCS_PATH}/ (general documents)")
    
    print(f"\n📋 Document Summary:")
    print(f"   • Total Documents: {len(documents)}")
    print(f"   • Successfully Processed: {len(successful_docs)}")
    print(f"   • Total Size: {sum(doc.get('file_size', 0) for doc in successful_docs) / 1024 / 1024:.1f} MB")
    
    print(f"\n💡 Alternative: Use Functions")
    print(f"Instead of importing all documents, you can use our Open WebUI functions:")
    print(f"   • Upload 'kb_status_checker.py' to check status")
    print(f"   • Upload 'simple_financial_search.py' for basic search")
    print(f"   • These will automatically access the embedded documents")

if __name__ == "__main__":
    main()