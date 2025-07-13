FROM python:3.11-slim

WORKDIR /app

# Copy core files
COPY core /app/core

# Copy financial_advisor directory
COPY financial_advisor /app/financial_advisor

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/core/requirements.txt

ENV PYTHONPATH /app

EXPOSE 8501 8502

# Copy startup script
COPY financial_advisor/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Start both Streamlit and Knowledge Base API
CMD ["/app/start.sh"]