FROM ubuntu:22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies and Python 3.11
RUN apt update && \
    apt install -y curl unzip wget gnupg lsb-release software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt update && \
    apt install -y python3.11 python3.11-venv python3.11-distutils python3-pip && \
    ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    ln -sf /usr/bin/pip3 /usr/bin/pip && \
    rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set working directory
WORKDIR /app

# Copy all app code
COPY . .

# Install Python dependencies with system break override
RUN pip install --upgrade pip && \
    pip install --break-system-packages -r requirements.txt

# Start Ollama in background, pull models, then launch your Python app
CMD bash -c "\
    ollama serve & \
    sleep 5 && \
    ollama pull llama3 && \
    ollama pull mistral && \
    python main.py"