FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt update && \
    apt install -y curl unzip && \
    rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy app code
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Start Ollama server in background, pull models, then run the main app
CMD sh -c "\
    ollama serve & \
    sleep 5 && \
    ollama pull llama3 && \
    ollama pull mistral && \
    python main.py"