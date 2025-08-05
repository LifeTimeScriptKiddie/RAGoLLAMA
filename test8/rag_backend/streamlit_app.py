import streamlit as st
import numpy as np
from pathlib import Path
import tempfile
import os
from api import query_ollama
from doc_processor import build_vectordb_from_pdf
from vectorizer import search_similar_chunks

st.set_page_config(
    page_title="RAG Document Chat",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'chunks' not in st.session_state:
    st.session_state.chunks = []
if 'embeddings' not in st.session_state:
    st.session_state.embeddings = np.array([])
if 'doc_chat_history' not in st.session_state:
    st.session_state.doc_chat_history = []
if 'general_chat_history' not in st.session_state:
    st.session_state.general_chat_history = []

st.title("📚 RAG Document Chat")
st.markdown("Upload a PDF document and chat with it using AI, or ask general questions")

# Create tabs for different functionalities
tab1, tab2 = st.tabs(["📄 Document Chat", "💬 General Chat"])

# Sidebar for document upload and settings
with st.sidebar:
    st.header("Document Upload")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf",
        help="Upload a PDF document to chat with"
    )
    
    if uploaded_file is not None:
        with st.spinner("Processing document..."):
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = Path(tmp_file.name)
            
            try:
                # Process the document
                chunks, embeddings = build_vectordb_from_pdf(tmp_path)
                st.session_state.chunks = chunks
                st.session_state.embeddings = embeddings
                st.success("✅ Document processed successfully!")
                
                # Store document name
                st.session_state.doc_name = uploaded_file.name
                
            except Exception as e:
                st.error(f"Error processing document: {e}")
            finally:
                # Clean up temp file
                os.unlink(tmp_path)
    
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
    if len(st.session_state.chunks) > 0:
        st.success(f"📄 Document loaded: {st.session_state.get('doc_name', 'Unknown')}")
    else:
        st.info("👆 Please upload a PDF document in the sidebar to get started")
        
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
        
        if len(st.session_state.chunks) > 0:
            # Document-based RAG response
            with st.spinner("Searching document and generating response..."):
                try:
                    # Retrieve relevant chunks using vectorizer
                    relevant_chunks = search_similar_chunks(
                        user_question,
                        st.session_state.embeddings,
                        st.session_state.chunks,
                        top_k=top_k
                    )
                    context = "\n\n".join(relevant_chunks)
                    
                    # Create RAG prompt
                    rag_prompt = f"""Based on the following context from the document, please answer the question.

Context:
{context}

Question: {user_question}

Answer:"""
                    
                    # Query the LLM
                    response = query_ollama(rag_prompt, selected_model)
                    
                    # Add AI response to doc chat history
                    st.session_state.doc_chat_history.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    st.error(f"Error generating response: {e}")
        else:
            # No document uploaded - inform user
            response = "Please upload a PDF document first to ask questions about it. You can use the 'General Chat' tab for general questions."
            st.session_state.doc_chat_history.append({"role": "assistant", "content": response})
        
        st.rerun()

# General Chat Tab
with tab2:
    st.markdown("### Ask Any Question")
    st.markdown("Chat with the AI without needing a document")
    
    # Chat input for general questions
    general_question = st.chat_input("Ask me anything...", key="general_chat")
    
    if general_question:
        # Add user message to general chat history
        st.session_state.general_chat_history.append({"role": "user", "content": general_question})
        
        with st.spinner("Generating response..."):
            try:
                # Query the LLM directly without RAG
                response = query_ollama(general_question, selected_model)
                
                # Add AI response to general chat history
                st.session_state.general_chat_history.append({"role": "assistant", "content": response})
                
            except Exception as e:
                st.error(f"Error generating response: {e}")
    
    # Display general chat history
    for message in st.session_state.general_chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
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