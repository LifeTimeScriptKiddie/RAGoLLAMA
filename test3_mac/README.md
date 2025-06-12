```
project-root/
├── docker-compose.yml
├── .env                     ← Optional: shared secrets
├── rag-backend/
│   ├── main.py
│   ├── config.py
│   ├── api.py
│   ├── uploader.py
│   ├── pdf_utils.py
│   ├── embed_utils.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env                 ← Backend-specific secrets
```

# Install ollama
```
brew install ollama
ollama pull llama3
ollama run llama3
ollama list

```
# Docker up and down
```
sudo docker compose up --build -d
sudo docker compose down
sudo docker ps
```







rag_backend → PORT 8501
open-webui → PORT 3000
ollama → PORT 11434

