# Folder Structure
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

# Reinstall Docker's official plugins (if needed)

```
sudo apt install --reinstall docker-buildx-plugin docker-compose-plugin

```
# Docker up and down
```
sudo docker compose up --build -d
sudo docker compose down
sudo docker ps
```


# Purge Conflicting Packages
```
sudo apt remove docker-buildx-plugin docker-compose-plugin
sudo apt clean
sudo apt install -f
sudo apt install docker-buildx docker-cli docker-compose
```


rag_backend → PORT 8501
open-webui → PORT 3000
ollama → PORT 11434

