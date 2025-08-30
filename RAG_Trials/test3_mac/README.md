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
ollama serve
ollama pull llama3
ollama pull codellama:7b           # for code generation
ollama pull mistral                # fast general-purpose
ollama pull phi3                  # small and performant

ollama run llama3
ollama list

```
# Docker up and down
```
sudo docker compose up --build -d
sudo docker compose down
sudo docker ps
```

# Docker Wipe out
```
sudo docker compose down --volumes --remove-orphans
sudo docker system prune -af --volumes
```





# Interface
```
rag_backend → PORT 8501
open-webui → PORT 3000
ollama → PORT 11434
```
