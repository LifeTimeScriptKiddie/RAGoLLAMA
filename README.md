
### 📈 Mermaid Diagram: Detailed RAG Pipeline

```mermaid
flowchart TD
    A1[PDF Uploaded via Open WebUI] --> B[File Stored in Volume]
    A2[PDF Uploaded via Streamlit Interface] --> B

    B --> C[Text Extraction or OCR using pdf_utils.py]
    C --> D[Text Splitting using RecursiveCharacterTextSplitter]
    D --> E[Embeddings generated via SentenceTransformer]
    E --> F[Embedded Chunks stored in Vector Database]

    G[User enters Query in Streamlit UI] --> H[Query Embedding using SentenceTransformer]
    H --> I[Top-k Similar Chunks Retrieved from Vector DB]
    I --> J[Prompt Constructed with Context and Question]
    J --> K[Prompt sent to Ollama API]
    K --> L[Response from Model displayed to User]

    F --> I
    J --> K



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
