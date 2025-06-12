
### 📈 Mermaid Diagram: Detailed RAG Pipeline

```mermaid
flowchart TD
    A[PDF File Uploaded via Streamlit Interface]
    B[Extract Text using PyPDF2 or OCR (ocrmypdf fallback)]
    C[Split Text into Chunks using RecursiveCharacterTextSplitter]
    D[Convert Chunks to Embeddings using SentenceTransformers]
    E[Store Embeddings in Temporary Vector Store (in memory)]
    F[User Inputs Query via Textbox]
    G[Embed Query using same Embedding Model]
    H[Perform Similarity Search against Vector Store]
    I[Select Top K Relevant Chunks]
    J[Construct Prompt: Context + User Query]
    K[Send Prompt to Local LLM via Ollama API]
    L[LLM Generates Response]
    M[Return Answer to User in Streamlit UI]

    %% Flow Connections
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

    %% Styling
    classDef step fill:#f9f9f9,stroke:#333,stroke-width:1px;
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
