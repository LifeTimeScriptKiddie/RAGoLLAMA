import streamlit as st
import requests
import os
from typing import Dict, List, Optional
import pandas as pd

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="RattGoLLAMA",
    page_icon="🦙",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    if "jwt_token" not in st.session_state:
        st.session_state.jwt_token = None
    if "user_info" not in st.session_state:
        st.session_state.user_info = None

def make_authenticated_request(method: str, endpoint: str, **kwargs) -> requests.Response:
    headers = kwargs.pop("headers", {})
    if st.session_state.jwt_token:
        headers["Authorization"] = f"Bearer {st.session_state.jwt_token}"
    
    url = f"{API_BASE_URL}{endpoint}"
    return requests.request(method, url, headers=headers, **kwargs)

def login_page():
    st.title("🦙 RattGoLLAMA Login")
    st.markdown("---")
    
    with st.form("login_form"):
        st.subheader("Login to RattGoLLAMA")
        username = st.text_input("Username", value="admin")
        password = st.text_input("Password", type="password", value="admin")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/auth/login",
                    json={"username": username, "password": password}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.jwt_token = data["access_token"]
                    st.session_state.user_info = {
                        "user_id": data["user_id"],
                        "username": data["username"],
                        "roles": data["roles"]
                    }
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Try admin/admin for demo.")
            except Exception as e:
                st.error(f"Login failed: {str(e)}")

def upload_page():
    st.subheader("📤 Upload Documents")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "docx", "txt", "xlsx", "xls"],
        help="Supported formats: PDF, DOCX, TXT, XLSX, XLS"
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("Upload File", type="primary"):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    response = make_authenticated_request("POST", "/upload", files=files)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"File uploaded successfully!")
                        st.json(data)
                        
                        # Trigger reindexing
                        reindex_response = make_authenticated_request(
                            "POST", "/ingest/reindex",
                            json={"document_id": data["id"]}
                        )
                        
                        if reindex_response.status_code == 200:
                            st.info("Document queued for processing...")
                    else:
                        st.error(f"Upload failed: {response.text}")
                        
                except Exception as e:
                    st.error(f"Upload error: {str(e)}")
        
        with col2:
            st.info(f"**File Details:**\n"
                   f"- Name: {uploaded_file.name}\n"
                   f"- Size: {uploaded_file.size:,} bytes\n"
                   f"- Type: {uploaded_file.type}")

def documents_page():
    st.subheader("📂 My Documents")
    
    try:
        response = make_authenticated_request("GET", "/documents")
        
        if response.status_code == 200:
            documents = response.json()
            
            if documents:
                # Create DataFrame for better display
                df_data = []
                for doc in documents:
                    df_data.append({
                        "ID": doc["id"],
                        "Filename": doc["original_filename"],
                        "Size": f"{doc['size']:,} bytes",
                        "Status": doc["status"],
                        "Uploaded": doc["created_at"][:19],  # Remove microseconds
                        "Processed": doc["processed_at"][:19] if doc["processed_at"] else "N/A"
                    })
                
                df = pd.DataFrame(df_data)
                
                # Color code status
                def style_status(val):
                    if val == "completed":
                        return "background-color: #90EE90"
                    elif val == "processing":
                        return "background-color: #FFD700"
                    elif val == "failed":
                        return "background-color: #FFB6C1"
                    else:
                        return "background-color: #E6E6FA"
                
                styled_df = df.style.applymap(style_status, subset=["Status"])
                st.dataframe(styled_df, use_container_width=True)
                
                # Reindex all button
                if st.button("🔄 Reindex All Documents"):
                    try:
                        response = make_authenticated_request("POST", "/ingest/reindex", json={})
                        if response.status_code == 200:
                            st.success("All documents queued for reindexing!")
                        else:
                            st.error("Reindexing failed")
                    except Exception as e:
                        st.error(f"Reindexing error: {str(e)}")
                        
            else:
                st.info("No documents uploaded yet.")
                
        else:
            st.error("Failed to fetch documents")
            
    except Exception as e:
        st.error(f"Error fetching documents: {str(e)}")

def search_page():
    st.subheader("🔍 Search Documents")
    
    with st.form("search_form"):
        query = st.text_input("Search Query", placeholder="Enter your search query...")
        limit = st.slider("Number of Results", min_value=1, max_value=50, value=10)
        submitted = st.form_submit_button("Search")
        
        if submitted and query.strip():
            try:
                response = make_authenticated_request(
                    "POST", "/search",
                    json={"query": query, "limit": limit}
                )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    st.write(f"Found {results['total']} results")
                    
                    if results["results"]:
                        for i, result in enumerate(results["results"], 1):
                            with st.expander(f"Result {i} - {result['filename']} (Score: {result['score']:.3f})"):
                                st.write(result["content"])
                                st.caption(f"Document ID: {result['document_id']}, Chunk: {result['chunk_index']}")
                    else:
                        st.info("No results found. Try uploading and processing some documents first.")
                else:
                    st.error("Search failed")
                    
            except Exception as e:
                st.error(f"Search error: {str(e)}")

def main_app():
    st.sidebar.markdown("## 🦙 RattGoLLAMA")
    st.sidebar.markdown("**RAG + JWT + LLM**")
    st.sidebar.markdown("---")
    
    # User info
    if st.session_state.user_info:
        st.sidebar.success(f"Welcome, {st.session_state.user_info['username']}!")
        if st.sidebar.button("Logout"):
            st.session_state.jwt_token = None
            st.session_state.user_info = None
            st.rerun()
    
    st.sidebar.markdown("---")
    
    # Navigation
    page = st.sidebar.radio(
        "Navigate",
        ["Upload", "Documents", "Search"]
    )
    
    # Main content
    st.title("🦙 RattGoLLAMA")
    st.markdown("**A small RAG system with JWT authentication**")
    st.markdown("---")
    
    if page == "Upload":
        upload_page()
    elif page == "Documents":
        documents_page()
    elif page == "Search":
        search_page()

def main():
    init_session_state()
    
    if st.session_state.jwt_token is None:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()