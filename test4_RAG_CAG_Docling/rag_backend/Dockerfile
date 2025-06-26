# Use a minimal Python 3.10 image
FROM python:3.10-slim

# Environment optimizations
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create working directory
WORKDIR /app

# Install system-level dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Only copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application source files
COPY . .

# Expose default Streamlit port
EXPOSE 8501

# Start Streamlit app (main.py is your entry point)
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]