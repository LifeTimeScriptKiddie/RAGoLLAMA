
### 📈 Mermaid Diagram: Detailed RAG Pipeline

```mermaid
flowchart TD
    A[PDF Uploaded via Streamlit]
    B[Extract text using PyPDF2 or OCR fallback]
    C[Split text using RecursiveCharacterTextSplitter]
    D[Generate embeddings with SentenceTransformers]
    E[Store embeddings in vector store]
    F[User inputs query via Streamlit]
    G[Embed query using same model]
    H[Similarity search against vector store]
    I[Select top K most relevant chunks]
    J[Construct prompt with context and user query]
    K[Send prompt to local LLM through Ollama]
    L[Receive generated answer from LLM]
    M[Display response in Streamlit]

    %% Flow connections
    A --> B
    B --> C
    C --> D
    D --> E
    F --> G
    G --> H
    E --> H
    H --> I
    I --> J
    F --> J
    J --> K
    K --> L
    L --> M

    %% Styling for clarity
    classDef step fill:#f0f0f0,stroke:#333,stroke-width:1px;
    class A,B,C,D,E,F,G,H,I,J,K,L,M step;

```

---

### 🧠 Summary of Key Steps

| Step | Description                                                                         |
| ---- | ----------------------------------------------------------------------------------- |
| A    | User uploads a `.pdf` through Streamlit.                                            |
| B    | Text is extracted using `PyPDF2`; if blank, fallback to `ocrmypdf`.                 |
| C    | Text is chunked using LangChain’s recursive splitter.                               |
| D    | Each chunk is converted into vector embeddings.                                     |
| E    | Embeddings are temporarily stored in memory (can be replaced with Chroma or FAISS). |
| F    | User submits a natural language question.                                           |
| G    | Question is also embedded.                                                          |
| H    | Embedding is compared against the vector DB to find similar chunks.                 |
| I    | Top-k most relevant text chunks are selected.                                       |
| J    | A prompt is constructed from those chunks + the question.                           |
| K    | The prompt is sent to a local model (e.g., `llama3`) running via Ollama.            |
| L    | Ollama generates the answer.                                                        |
| M    | Answer is shown to the user in Streamlit.                                           |
