
Working on followings,


# From test3_mac

- Layer	Tool / Method
```
  Document Parsing	PyPDF2 + OCR + Manual Split
  UI	Streamlit
  LLM Backend	Ollama via query_ollama()
  Prompting	Inject top-N chunked text as prompt
  Retrieval	Basic string-injection (not vector-based)
  Speed Tradeoff	Long wait due to full text tokenization
```

# To test4_RAG_CAG_Docling - Target Architecture
```
Layer	Replace with / Add
Document Parsing	-  DoclingLoader
Vector Search	-  Chroma + LangChain retriever
Prompting	-  LangChain RAG_CAG chain
LLM Backend	 - Ollama (via custom wrapper)
UI	-  Same Streamlit UI
Speed Tradeoff	-  Only relevant chunks sent to LLM (fast)
```

# “RAG-CAG” means:
```
•	Only the top-k retrieved chunks (from Chroma) are passed.
•	LangChain handles chunk retrieval + question injection + optional citation formatting.
•	Faster than sending the whole document or 3k+ tokens to Ollama.
•	More accurate than manual string injection.
```

# Implementation Plan

```
File	Change
pdf_utils.py	Replace extract_text_from_pdf() and split_text_into_chunks() with build_vectordb_from_pdf() using DoclingLoader
api.py	Keep query_ollama() as-is
main.py	Wrap query_ollama() with LangChain’s RetrievalQAWithSourcesChain using a custom LLM class
requirements.txt	Add langchain, chromadb, docling, and their dependencies

```
