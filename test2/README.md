
```
project-root/
├── docker-compose.yml
├── .env                   ← Optional: Shared environment config
├── rag-backend/           ← Python RAG backend (this is the container you’re asking about)
│   ├── main.py
│   ├── config.py
│   ├── api.py
│   ├── uploader.py
│   ├── pdf_utils.py
│   ├── embed_utils.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env               ← Backend-specific secrets (optional)
```


docker-compose up --build -d

docker-compose down


