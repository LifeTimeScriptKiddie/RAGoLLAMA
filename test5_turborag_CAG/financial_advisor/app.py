
import streamlit as st, sqlite3, pandas as pd
from core.ingestion import ingest
from core.vector_store import add, query
from core.statement_parser import ingest_statement
from core.categorizer import tag_business
from core.tax_optimizer import optimize

st.title("Financial Advisor Suite")
tabs = st.tabs(["RAG", "Tax Dashboard"])

conn = sqlite3.connect("/app/data/finance.db", check_same_thread=False)

with tabs[0]:
    st.subheader("RAG Q&A")
    uploaded = st.file_uploader("Upload document", key="doc")
    if uploaded:
        tmp = "/tmp/doc"
        with open(tmp, "wb") as f:
            f.write(uploaded.getbuffer())
        docs = ingest(tmp)
        add([d.text for d in docs])
        st.success("Document indexed.")
    q = st.text_input("Ask a question")
    if q:
        res = query(q)
        for txt, dist in res:
            st.markdown(f"**Distance:** {{dist:.4f}}")
            st.write(txt[:400] + "...")


with tabs[1]:
    st.subheader("Tax Dashboard")
    stmt = st.file_uploader("Upload statement (PDF/CSV/OFX)", type=["pdf","csv","ofx"], key="stmt")
    if stmt:
        tmp = "/tmp/stmt"
        with open(tmp, "wb") as f:
            f.write(stmt.getbuffer())
        df = ingest_statement(tmp)
        mapping = {
            "BizA": ["office_supplies", "meals_travel"],
            "BizB": ["auto_expense"],
            "BizC": ["software"],
            "BizD": ["unclassified"],
        }
        df = tag_business(df, mapping)
        df.to_sql("transactions", conn, if_exists="append", index=False)
        st.success(f"{len(df)} rows processed.")
    if 'transactions' in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        df = pd.read_sql("SELECT * FROM transactions", conn)
        st.dataframe(df)
        if st.button("Run Optimizer"):
            sugg = optimize(df)
            st.dataframe(sugg)

