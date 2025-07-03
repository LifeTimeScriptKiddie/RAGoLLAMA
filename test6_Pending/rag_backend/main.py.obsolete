import streamlit as st
from pathlib import Path
import tempfile
from langchain_docling.loader import DoclingLoader, ExportType
from local_embed import embed_chunks, search_similar_chunks
from api import query_ollama

st.set_page_config(page_title="RAG Helper", layout="centered")
st.title("🧠 RAG Helper: PDF Q&A with SentenceTransformers + Ollama")

# --- File Upload ---
uploaded_file = st.file_uploader("📄 Upload a PDF file", type=["pdf"])

if uploaded_file:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            pdf_path = Path(tmp.name)

        # Step 1: Chunk the PDF using Docling
        loader = DoclingLoader(file_path=[str(pdf_path)], export_type=ExportType.DOC_CHUNKS)
        docs = loader.load()
        chunks = [doc.page_content for doc in docs]

        # Step 2: Embed all chunks using local model
        st.info("🔍 Embedding chunks...")
        chunk_embeddings = embed_chunks(chunks)

        # Step 3: Ask a question
        question = st.text_input("💬 Ask a question about this document:")
        if st.button("🚀 Query Document"):
            with st.spinner("Thinking..."):
                top_chunks = search_similar_chunks(question, chunk_embeddings, chunks, top_k=3)
                context = "\n\n".join(top_chunks)

                prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
                answer = query_ollama(prompt)

                st.subheader("🧾 Answer")
                st.markdown(answer)

                st.subheader("📌 Top Chunks Used")
                for i, chunk in enumerate(top_chunks, 1):
                    st.markdown(f"**Chunk {i}:**")
                    st.code(chunk[:500] + "..." if len(chunk) > 500 else chunk)

    except Exception as e:
        st.error(f"❌ An error occurred: {e}")