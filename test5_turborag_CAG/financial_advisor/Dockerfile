FROM python:3.11-slim

WORKDIR /app

# Copy core files
COPY core /app/core

# Copy financial_advisor directory
COPY financial_advisor /app/financial_advisor

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/core/requirements.txt -r /app/financial_advisor/requirements.txt

EXPOSE 8501

# Start Streamlit
CMD ["streamlit", "run", "/app/financial_advisor/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]