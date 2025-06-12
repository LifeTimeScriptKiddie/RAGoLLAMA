
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
Here's a simplified summary:

**RAG Pipeline**

1. **Upload PDF**
	* Upload a PDF to the system.
2. **Text Extraction / OCR**
	* Extract text from the PDF if it's text-based, or use OCR (if implemented) for image-based PDFs.
3. **Chunking**
	* Split the text into smaller overlapping pieces.
4. **Embedding + Similarity Search**
	* Embed chunks and compare them to a query vector to find the top `k` most similar chunks.
5. **Prompt Construction**
	* Create a new prompt using the top `k` relevant chunks and the original query.
6. **LLM Query (Ollama)**
	* Send the prompt to Ollama's model (e.g., `llama3`) and get a context-aware answer.
