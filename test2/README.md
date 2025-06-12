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


# Wipe out
sudo docker compose down --volumes --remove-orphans
sudo docker system prune -af --volumes

```


# Purge Conflicting Packages
```
sudo apt remove docker-buildx-plugin docker-compose-plugin
sudo apt clean
sudo apt install -f
sudo apt install docker-buildx docker-cli docker-compose
```

# Interface
```
rag_backend → PORT 8501
open-webui → PORT 3000
ollama → PORT 11434
```


# Pulling ollama model inside container
```
docker exec -it ollama ollama pull llama3
docker exec -it ollama ollama pull llama3:8b-instruct
docker exec -it ollama ollama pull codellama:7b           # for code generation
docker exec -it ollama ollama pull mistral                # fast general-purpose
docker exec -it ollama ollama pull phi3                  # small and performant

```
# Check ollama model
```
docker exec -it ollama ollama list
```

