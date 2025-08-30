import streamlit as st
import requests
import json
import os
from typing import Dict, Any, List
import time

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_TOKEN = st.session_state.get("api_token", None)

def get_auth_headers() -> Dict[str, str]:
    """Get authentication headers."""
    if API_TOKEN:
        return {"Authorization": f"Bearer {API_TOKEN}"}
    return {}

def call_backend(endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
    """Make API call to backend."""
    url = f"{BACKEND_URL}{endpoint}"
    headers = get_auth_headers()
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, headers=headers, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        if response.status_code == 401:
            st.error("Authentication required. Please login.")
            st.session_state["api_token"] = None
            st.rerun()
            
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to backend at {BACKEND_URL}")
        return {"error": "Connection failed"}
    except requests.exceptions.Timeout:
        st.error("Request timed out")
        return {"error": "Timeout"}
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")
        return {"error": str(e)}

def upload_document(file) -> Dict[str, Any]:
    """Upload document to backend."""
    url = f"{BACKEND_URL}/upload/document"
    headers = get_auth_headers()
    
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        response = requests.post(url, headers=headers, files=files, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def main():
    st.set_page_config(
        page_title="RAG-Ollama System",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 RAG-Ollama System")
    st.markdown("---")
    
    # Sidebar for system status and auth
    with st.sidebar:
        st.header("System Status")
        
        # Backend health check
        health = call_backend("/admin/health")
        if "error" not in health:
            st.success("✅ Backend Online")
        else:
            st.error("❌ Backend Offline")
            st.json(health)
        
        st.markdown("---")
        
        # Authentication section (placeholder)
        st.header("Authentication")
        if not API_TOKEN:
            st.info("🔐 Authentication not implemented yet")
            # For demo purposes, set a placeholder token
            if st.button("Use Demo Mode"):
                st.session_state["api_token"] = "demo-token"
                st.rerun()
        else:
            st.success("✅ Authenticated (Demo Mode)")
            if st.button("Logout"):
                st.session_state["api_token"] = None
                st.rerun()
    
    # Main content tabs
    if API_TOKEN:
        tab1, tab2, tab3, tab4 = st.tabs(["💬 Query", "📁 Upload", "📊 Admin", "📈 Monitoring"])
        
        # Query Tab
        with tab1:
            st.header("Document Query")
            
            query_text = st.text_area(
                "Enter your question:",
                height=100,
                placeholder="Ask a question about your documents..."
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                k_results = st.number_input("Results", min_value=1, max_value=20, value=5)
            
            if st.button("🔍 Query", type="primary", disabled=not query_text.strip()):
                with st.spinner("Processing query..."):
                    start_time = time.time()
                    
                    result = call_backend("/query/", "POST", {
                        "query": query_text,
                        "k": k_results
                    })
                    
                    query_time = time.time() - start_time
                    
                    if "error" not in result:
                        st.success(f"✅ Query completed in {query_time:.2f}s")
                        
                        # Display answer
                        st.subheader("Answer")
                        st.write(result.get("answer", "No answer provided"))
                        
                        # Display sources
                        if result.get("sources"):
                            st.subheader("Sources")
                            for i, source in enumerate(result["sources"], 1):
                                with st.expander(f"Source {i}"):
                                    st.json(source)
                        
                        # Display metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Query Time", f"{query_time:.2f}s")
                        with col2:
                            st.metric("Latency (Backend)", f"{result.get('latency_ms', 0):.0f}ms")
                        with col3:
                            st.metric("Sources Found", len(result.get("sources", [])))
                    else:
                        st.error(f"Query failed: {result['error']}")
        
        # Upload Tab
        with tab2:
            st.header("Document Upload")
            
            uploaded_file = st.file_uploader(
                "Choose a document to upload",
                type=['pdf', 'txt', 'doc', 'docx'],
                help="Supported formats: PDF, TXT, DOC, DOCX"
            )
            
            if uploaded_file is not None:
                st.write("**File Details:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Name:** {uploaded_file.name}")
                with col2:
                    st.write(f"**Size:** {len(uploaded_file.getvalue())/1024:.1f} KB")
                with col3:
                    st.write(f"**Type:** {uploaded_file.type}")
                
                if st.button("📤 Upload Document", type="primary"):
                    with st.spinner("Uploading and processing document..."):
                        result = upload_document(uploaded_file)
                        
                        if "error" not in result:
                            st.success("✅ Document uploaded successfully!")
                            st.json(result)
                        else:
                            st.error(f"Upload failed: {result['error']}")
        
        # Admin Tab  
        with tab3:
            st.header("System Administration")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Index Management")
                
                if st.button("📊 Index Info"):
                    info = call_backend("/admin/index/info")
                    if "error" not in info:
                        st.json(info)
                    else:
                        st.error(f"Failed to get index info: {info['error']}")
                
                if st.button("📸 Create Snapshot"):
                    result = call_backend("/admin/index/snapshot", "POST")
                    if "error" not in result:
                        st.success("Snapshot created!")
                        st.json(result)
                    else:
                        st.error(f"Snapshot failed: {result['error']}")
            
            with col2:
                st.subheader("Model Management")
                
                if st.button("🤖 List Models"):
                    models = call_backend("/admin/models")
                    if "error" not in models:
                        st.json(models)
                    else:
                        st.error(f"Failed to get models: {models['error']}")
        
        # Monitoring Tab
        with tab4:
            st.header("System Monitoring")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Quick Metrics")
                
                # Refresh button
                if st.button("🔄 Refresh Metrics"):
                    st.rerun()
                
                # Placeholder metrics (would come from actual backend)
                st.metric("Total Documents", "0", "0")
                st.metric("Total Chunks", "0", "0") 
                st.metric("Index Size", "0 MB", "0")
            
            with col2:
                st.subheader("External Dashboards")
                
                st.markdown("""
                - 📊 [Prometheus](http://localhost:9090) - Metrics collection
                - 📈 [Grafana](http://localhost:3000) - Visualization dashboards
                - 🔍 [Backend API Docs](http://localhost:8000/docs) - API documentation
                """)
    else:
        st.info("🔐 Please authenticate to use the RAG system.")
        st.markdown("""
        ### Features:
        - 💬 **Query Interface**: Ask questions about uploaded documents
        - 📁 **Document Upload**: Upload PDFs, text files, and Word documents  
        - 📊 **Administration**: Manage index, snapshots, and models
        - 📈 **Monitoring**: View system metrics and dashboards
        
        Click "Use Demo Mode" in the sidebar to get started.
        """)

if __name__ == "__main__":
    main()