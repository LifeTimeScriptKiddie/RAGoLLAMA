
FROM python:3.11-slim
WORKDIR /app
COPY ../core /app/core
COPY . /app/market_researcher
RUN pip install --no-cache-dir -r /app/core/requirements.txt -r /app/market_researcher/requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "/app/market_researcher/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
