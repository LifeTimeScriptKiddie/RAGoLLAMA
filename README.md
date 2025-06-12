
### 📈 Mermaid Diagram: Detailed RAG Pipeline

```mermaid
flowchart TD
    A1[PDF Uploaded via Open WebUI] --> B[File Stored on Volume]
    A2[PDF Uploaded via Streamlit Interface] --> B

    B --> C[Text Extraction / OCR (pdf_utils.py)]
    C --> D[Text Splitting (RecursiveCharacterTextSplitter)]
    D --> E[Vector Embedding (SentenceTransformer)]
    E --> F[Vector DB (in-memory or persistent store)]

    G[User Query from Streamlit] --> H[Query Embedding]
    H --> I[Top-k Similar Chunk Search]
    I --> J[Prompt Built with Context]
    J --> K[Ollama API Called for Completion]

    F --> I
    J --> K
    K --> L[Answer Returned to User]

    style A1 fill:#d0e1ff,stroke:#3366cc
    style A2 fill:#d0e1ff,stroke:#3366cc
    style B fill:#f0f0f0,stroke:#999999
    style C fill:#fff2cc,stroke:#cc9900
    style D fill:#fff2cc,stroke:#cc9900
    style E fill:#d9ead3,stroke:#6aa84f
    style F fill:#cfe2f3,stroke:#3d85c6
    style G fill:#d9d2e9,stroke:#8e7cc3
    style H fill:#d9d2e9,stroke:#8e7cc3
    style I fill:#cfe2f3,stroke:#3d85c6
    style J fill:#f9cb9c,stroke:#e69138
    style K fill:#ead1dc,stroke:#c27ba0
    style L fill:#d0e0e3,stroke:#6d9eeb


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
