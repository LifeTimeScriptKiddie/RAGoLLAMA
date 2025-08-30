import streamlit as st
from pathlib import Path
import tempfile
from pdf_utils import extract_text_from_pdf
from api import query_ollama

st.set_page_config(page_title="RAG Helper", layout="centered")
st.title("🧠 RAG Helper: PDF Q&A with Ollama")

# Step 1: File Upload
uploaded_file = st.file_uploader("📄 Upload a PDF file", type=["pdf"])

if uploaded_file:
    try:
        # Step 2: Save PDF to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            pdf_path = Path(tmp.name)

        # Step 3: Extract Text
        text = extract_text_from_pdf(pdf_path)
        if not text:
            st.error("⚠️ Could not extract any text from the PDF.")
        else:
            st.subheader("📚 Extracted Text")
            st.code(text[:1000] + "..." if len(text) > 1000 else text)

            # Step 4: Ask a question
            question = st.text_input("💬 Ask a question about this document:")
            if st.button("🚀 Query Ollama"):
                with st.spinner("Thinking..."):
                    prompt = f"Context:\n{text[:3000]}\n\nQuestion: {question}\nAnswer:"
                    answer = query_ollama(prompt)
                    st.subheader("🧾 Answer")
                    st.markdown(answer)
    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
