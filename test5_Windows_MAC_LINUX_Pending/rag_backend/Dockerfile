FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies and Python 3.11
RUN apt update && \
    apt install -y curl unzip wget gnupg software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt update && \
    apt install -y python3.11 python3.11-venv python3.11-distutils python3-pip && \
    ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip && \
    rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set working directory
WORKDIR /app

# Copy app code
COPY . .

# Install Python dependencies with workaround for blinker
RUN pip install --upgrade pip && \
    pip install --break-system-packages --ignore-installed blinker && \
    pip install --break-system-packages -r requirements.txt

# Start Ollama in background, pull models, and run main
CMD bash -c "\
    ollama serve & \
    sleep 5 && \
    ollama pull mistral && \
    python3 main.py"
    
    