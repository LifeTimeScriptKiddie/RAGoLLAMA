import streamlit as st
import os
from backend_client import BackendClient

st.set_page_config(
    page_title="RAG Document Chat",
    page_icon="📚",
    layout="wide"
)

# Initialize backend client
@st.cache_resource
def get_backend_client():
    return BackendClient()

backend_client = get_backend_client()

# Initialize session state
if 'current_document' not in st.session_state:
    st.session_state.current_document = None
if 'doc_chat_history' not in st.session_state:
    st.session_state.doc_chat_history = []
if 'general_chat_history' not in st.session_state:
    st.session_state.general_chat_history = []
if 'documents' not in st.session_state:
    st.session_state.documents = []

st.title("📚 RAG Document Chat")
st.markdown("Upload a PDF document and chat with it using AI, or ask general questions")

# Create tabs for different functionalities
tab1, tab2 = st.tabs(["📄 Document Chat", "💬 General Chat"])

# Check backend health
if not backend_client.health_check():
    st.error("❌ Backend server is not available. Please check your backend service.")
    st.stop()

# Sidebar for document management and settings
with st.sidebar:
    st.header("Document Management")
    
    # Document upload
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf",
        help="Upload a PDF document to chat with"
    )
    
    if uploaded_file is not None:
        with st.spinner("Uploading and processing document..."):
            try:
                # Upload to backend
                file_content = uploaded_file.read()
                result = backend_client.upload_document(file_content, uploaded_file.name)
                
                st.success(f"✅ Document uploaded: {uploaded_file.name}")
                st.session_state.current_document = result
                
                # Refresh document list
                st.session_state.documents = backend_client.list_documents()
                
            except Exception as e:
                st.error(f"Error uploading document: {e}")
    
    # Document selection
    st.header("Select Document")
    
    # Refresh documents list
    if st.button("🔄 Refresh Documents"):
        st.session_state.documents = backend_client.list_documents()
    
    # Show available documents
    if st.session_state.documents:
        doc_options = {doc["filename"]: doc for doc in st.session_state.documents}
        selected_doc_name = st.selectbox(
            "Available Documents",
            options=list(doc_options.keys()),
            index=0 if st.session_state.current_document is None else 
                  list(doc_options.keys()).index(st.session_state.current_document["filename"]) 
                  if st.session_state.current_document and st.session_state.current_document["filename"] in doc_options 
                  else 0
        )
        
        if selected_doc_name:
            st.session_state.current_document = doc_options[selected_doc_name]
            
            # Show document info
            doc = st.session_state.current_document
            st.info(f"""
            **Document:** {doc['filename']}
            **Status:** {doc['status']}
            **Chunks:** {doc['chunk_count']}
            **Uploaded:** {doc['created_at'][:19]}
            """)
            
            # Delete document button
            if st.button("🗑️ Delete Document", type="secondary"):
                if backend_client.delete_document(doc['id']):
                    st.success("Document deleted!")
                    st.session_state.current_document = None
                    st.session_state.documents = backend_client.list_documents()
                    st.rerun()
                else:
                    st.error("Failed to delete document")
    else:
        st.info("No documents uploaded yet")
    
    # Model selection
    st.header("Model Settings")
    model_options = ["llama3", "mistral", "codellama", "gemma", "orca-mini"]
    selected_model = st.selectbox(
        "Select LLM Model",
        model_options,
        index=0
    )
    
    # RAG settings
    st.header("RAG Settings")
    top_k = st.slider("Number of chunks to retrieve", 1, 10, 3)
    chunk_size = st.slider("Chunk size", 500, 2000, 1000, step=100)

# Document Chat Tab
with tab1:
    if st.session_state.current_document and st.session_state.current_document['status'] == 'completed':
        st.success(f"📄 Document loaded: {st.session_state.current_document['filename']}")
    else:
        st.info("👆 Please upload and select a PDF document in the sidebar to get started")
        
        # Show example questions
        st.markdown("### Example Questions You Can Ask About Documents:")
        st.markdown("""
        - What is the main topic of this document?
        - Can you summarize the key points?
        - What are the conclusions mentioned?
        - Explain the methodology used
        - What are the recommendations?
        """)
    
    # Display doc chat history
    for message in st.session_state.doc_chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input for document (always show)
    user_question = st.chat_input("Ask a question about your document...", key="doc_chat")
    
    if user_question:
        # Add user message to doc chat history
        st.session_state.doc_chat_history.append({"role": "user", "content": user_question})
        
        if st.session_state.current_document and st.session_state.current_document['status'] == 'completed':
            # Document-based RAG response using backend
            with st.spinner("Searching document and generating response..."):
                try:
                    response = backend_client.chat_with_document(
                        message=user_question,
                        document_id=st.session_state.current_document['id'],
                        model=selected_model,
                        top_k=top_k
                    )
                    
                    # Add AI response to doc chat history
                    st.session_state.doc_chat_history.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"Error generating response: {e}"
                    st.session_state.doc_chat_history.append({"role": "assistant", "content": error_msg})
        else:
            # No document selected - inform user
            response = "Please upload and select a PDF document first to ask questions about it. You can use the 'General Chat' tab for general questions."
            st.session_state.doc_chat_history.append({"role": "assistant", "content": response})
        
        st.rerun()

# General Chat Tab
with tab2:
    st.markdown("### Ask Any Question")
    st.markdown("Chat with the AI without needing a document")
    
    # Display general chat history
    for message in st.session_state.general_chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input for general questions
    general_question = st.chat_input("Ask me anything...", key="general_chat")
    
    if general_question:
        # Add user message to general chat history
        st.session_state.general_chat_history.append({"role": "user", "content": general_question})
        
        with st.spinner("Generating response..."):
            try:
                # Use backend for general chat
                response = backend_client.general_chat(general_question, selected_model)
                
                # Add AI response to general chat history
                st.session_state.general_chat_history.append({"role": "assistant", "content": response})
                
            except Exception as e:
                error_msg = f"Error generating response: {e}"
                st.session_state.general_chat_history.append({"role": "assistant", "content": error_msg})
        
        st.rerun()
    
    if len(st.session_state.general_chat_history) == 0:
        st.markdown("### Example Questions:")
        st.markdown("""
        - Explain quantum computing in simple terms
        - Write a Python function to sort a list
        - What are the benefits of renewable energy?
        - How does machine learning work?
        - Tell me a joke
        """)

# Footer
st.markdown("---")
st.markdown("Built with Streamlit, Ollama, and LangChain | Running alongside Open WebUI")