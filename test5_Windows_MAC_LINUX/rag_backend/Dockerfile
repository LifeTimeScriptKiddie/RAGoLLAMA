FROM ubuntu:22.04

# Prevent interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Update and install dependencies
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

# Copy application code
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Start Ollama, pull models, then run your Python app
CMD bash -c "\
    ollama serve & \
    sleep 5 && \
    ollama pull llama3 && \
    ollama pull mistral && \
    python main.py"