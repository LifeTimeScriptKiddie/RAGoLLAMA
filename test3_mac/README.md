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
ollama run llama3

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

