import streamlit as st
from pathlib import Path
import tempfile
from pdf_utils import extract_text_from_pdf
from api import query_ollama

st.title("RAG Helper")

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        pdf_path = Path(tmp.name)

    text = extract_text_from_pdf(pdf_path)

    st.subheader("Extracted Text")
    st.code(text[:1000] + "..." if len(text) > 1000 else text)

    question = st.text_input("Ask a question:")
    if st.button("Query Ollama"):
        prompt = f"Context:\n{text[:3000]}\n\nQuestion: {question}\nAnswer:"
        answer = query_ollama(prompt)
        st.subheader("Answer")
        st.markdown(answer)
