
import streamlit as st
from core.ingestion import ingest
from core.vector_store import query, add

st.title("TurboRAG Explorer")
uploaded = st.file_uploader("Upload document")
if uploaded:
    tmp='/tmp/doc'
    with open(tmp,'wb') as f:
        f.write(uploaded.getbuffer())
    docs = ingest(tmp)
    add([d.text for d in docs])
    st.success("Indexed!")
q = st.text_input("Ask question")
if q:
    res = query(q)
    for txt, dist in res:
        st.markdown(f"**Dist** {{dist:.3f}}")
        st.write(txt[:400]+"...")
