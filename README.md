

### 📊 **Mermaid Diagram for Your RAG Pipeline**

```mermaid
flowchart TD
    A[📄 PDF Input] --> B[📝 Text Extraction]
    B --> C[🔪 Chunking]
    C --> D[🔢 Embedding]
    D --> E[🧠 Vector DB]
    E --> F[🔍 Similarity Search]
    F --> G[🧾 Prompt Construction]
    G --> H[🤖 LLM Response]

    style A fill:#fef9c3,stroke:#000
    style B fill:#fce7f3,stroke:#000
    style C fill:#e0f2fe,stroke:#000
    style D fill:#ede9fe,stroke:#000
    style E fill:#d1fae5,stroke:#000
    style F fill:#fcd34d,stroke:#000
    style G fill:#f3e8ff,stroke:#000
    style H fill:#dbeafe,stroke:#000

```

---

### 🧠 How It Works – Step by Step

| Step                       | Description                                                                                            |
| -------------------------- | ------------------------------------------------------------------------------------------------------ |
| **📄 PDF Input**           | The user uploads a `.pdf` file.                                                                        |
| **📝 Text Extraction**     | Text is extracted from the PDF using `PyPDF2`, or `ocrmypdf` if it's image-based.                      |
| **🔪 Chunking**            | The text is broken into overlapping segments using LangChain's `RecursiveCharacterTextSplitter`.       |
| **🔢 Embedding**           | Each chunk is embedded into a vector using SentenceTransformers.                                       |
| **🧠 Vector DB**           | All embeddings are stored temporarily (in memory or file-based).                                       |
| **🔍 Similarity Search**   | When a question is asked, its embedding is compared against the vector DB to retrieve relevant chunks. |
| **🧾 Prompt Construction** | The top-k chunks are inserted into a prompt with the user's question.                                  |
| **🤖 LLM Response**        | The prompt is sent to Ollama’s local LLM for generation.                                               |

---
