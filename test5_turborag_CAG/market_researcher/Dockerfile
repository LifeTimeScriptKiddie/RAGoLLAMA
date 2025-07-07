FROM python:3.11-slim

WORKDIR /app

# Copy shared dependencies
COPY core /app/core

# Copy market_researcher-specific code
COPY market_researcher /app/market_researcher

# Install dependencies
RUN pip install --no-cache-dir -r /app/core/requirements.txt -r /app/market_researcher/requirements.txt

EXPOSE 8501

# Run the app
CMD ["streamlit", "run", "/app/market_researcher/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]