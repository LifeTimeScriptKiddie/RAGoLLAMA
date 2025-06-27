# Use a minimal Python 3.10 image
FROM python:3.10-slim

# Avoid writing .pyc files and enable unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=America/New_York

# Set working directory
WORKDIR /app

# Install system tools including OCR and cron
RUN apt-get update && apt-get install -y \
    build-essential \
    poppler-utils \
    tesseract-ocr \
    ocrmypdf \
    cron \
    curl \
    tzdata \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Copy crontab and register it
COPY crontab.txt /etc/cron.d/uploader-cron
RUN chmod 0644 /etc/cron.d/uploader-cron && \
    crontab /etc/cron.d/uploader-cron

# Run cron in foreground (keeps container alive)
CMD ["cron", "-f"]