#!/usr/bin/env python3
"""
Browser Opener for Multi-RAG Pipeline

Automatically opens web browsers to access the Multi-RAG interfaces.
"""

import webbrowser
import time
import requests
import sys
from urllib.parse import urljoin

def wait_for_service(url, timeout=60, service_name="service"):
    """Wait for a service to become available."""
    print(f"⏳ Waiting for {service_name} at {url}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name} is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(2)
    
    print(f"❌ {service_name} did not become ready within {timeout} seconds")
    return False

def open_multi_rag_interfaces():
    """Open web browsers for Multi-RAG interfaces."""
    
    print("🚀 Multi-RAG Document Pipeline - Browser Opener")
    print("=" * 50)
    
    # Service URLs
    api_url = "http://localhost:8000"
    streamlit_url = "http://localhost:8501"
    api_docs_url = "http://localhost:8000/docs"
    
    # Wait for services to be ready
    services = [
        (api_url + "/health", "API Service"),
        (streamlit_url, "Streamlit Interface")
    ]
    
    all_ready = True
    for url, name in services:
        if not wait_for_service(url, timeout=30, service_name=name):
            all_ready = False
    
    if not all_ready:
        print("\n❌ Some services are not ready. Please check:")
        print("   docker-compose ps")
        print("   docker-compose logs")
        return False
    
    print("\n🌐 Opening web interfaces...")
    
    # Open interfaces
    interfaces = [
        (streamlit_url, "📊 Streamlit Dashboard"),
        (api_docs_url, "📖 API Documentation"),
        (api_url, "🔧 API Endpoints")
    ]
    
    for url, description in interfaces:
        try:
            print(f"   Opening {description}: {url}")
            webbrowser.open(url)
            time.sleep(1)  # Small delay between opens
        except Exception as e:
            print(f"   ❌ Failed to open {url}: {e}")
    
    print("\n🎉 Multi-RAG Pipeline is ready!")
    print("\n📋 Available Interfaces:")
    print(f"   • Streamlit Dashboard: {streamlit_url}")
    print(f"   • API Documentation:   {api_docs_url}")
    print(f"   • API Endpoints:       {api_url}")
    print(f"   • Health Check:        {api_url}/health")
    
    print("\n💡 Quick Start Tips:")
    print("   1. Use the Streamlit interface for interactive document processing")
    print("   2. Check the API docs for programmatic access")
    print("   3. Upload documents via the web interface or API")
    print("   4. Compare Docling vs Microsoft RAG embeddings")
    
    return True

def main():
    """Main function."""
    try:
        success = open_multi_rag_interfaces()
        if success:
            print("\n✨ All interfaces opened successfully!")
        else:
            print("\n⚠️  Some interfaces may not be available.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()