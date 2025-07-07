
FROM python:3.11-slim
WORKDIR /app
COPY core /app/core
COPY . /app/financial_advisor
RUN pip install --no-cache-dir -r /app/core/requirements.txt -r /app/financial_advisor/requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "/app/financial_advisor/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
