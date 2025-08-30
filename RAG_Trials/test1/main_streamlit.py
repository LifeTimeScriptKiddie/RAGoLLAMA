import streamlit as st
from sentence_transformers import SentenceTransformer
import numpy as np
import json
from pathlib import Path
from PyPDF2 import PdfReader
import subprocess
import logging
import tempfile

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

st.set_page_config(page_title="RAG QA with PDF Knowledge", layout="wide")
st.title("📄 RAG QA on Your PDFs")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        pdf_path = Path(tmp.name)

    # Extract text from PDF
    try:
        reader = PdfReader(str(pdf_path))
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        st.stop()

    # Split into chunks
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = splitter.create_documents([text])
    chunks = [doc.page_content for doc in docs]

    # Embed chunks
    chunk_embeddings = model.encode(chunks)

    # Query interface
    query = st.text_input("Ask a question about your PDF:")
    if query:
        query_vec = model.encode(query)
        similarities = [np.dot(query_vec, emb) / (np.linalg.norm(query_vec) * np.linalg.norm(emb)) for emb in chunk_embeddings]
        top_indices = np.argsort(similarities)[::-1][:3]

        top_chunks = [chunks[i] for i in top_indices]
        st.subheader("🔍 Top Matching Chunks")
        for i, chunk in enumerate(top_chunks):
            st.markdown(f"**Chunk {i+1} (Score: {similarities[top_indices[i]]:.2f}):**")
            st.code(chunk)

        # Display full prompt
        context_str = "\n---\n".join(top_chunks)
        prompt = f"""Context:
{context_str}

Question: {query}
Answer:"""

        st.subheader("🧠 Final Prompt to Send to LLM")
        st.code(prompt)

        # Optionally: send to Ollama or external LLM
        if st.button("🧠 Query Local LLM (Ollama)"):
            try:
                result = subprocess.run(
                    ["ollama", "run", "llama3"],
                    input=prompt,
                    text=True,
                    capture_output=True,
                    check=True
                )
                st.subheader("🤖 LLM Response")
                st.markdown(result.stdout.strip())
            except subprocess.CalledProcessError as e:
                st.error(f"Error running Ollama: {e.stderr}")
