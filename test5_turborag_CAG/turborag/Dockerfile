FROM python:3.11-slim

WORKDIR /app

# Copy shared code and requirements
COPY core /app/core

# Copy only the turborag app folder
COPY turborag /app/turborag

# Install dependencies
RUN pip install --no-cache-dir -r /app/core/requirements.txt -r /app/turborag/requirements.txt

EXPOSE 8501

# Start Streamlit app
CMD ["streamlit", "run", "/app/turborag/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]