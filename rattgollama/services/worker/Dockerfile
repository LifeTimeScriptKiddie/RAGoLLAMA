FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including CUDA support
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker script
COPY worker.py .

# Run the worker
CMD ["python", "worker.py"]