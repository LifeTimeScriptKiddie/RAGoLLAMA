# Use Ubuntu as the base image
FROM ubuntu:22.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=America/New_York

# Set working directory
WORKDIR /app

# Install system packages and Python 3.10
RUN apt-get update && \
    apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    build-essential \
    poppler-utils \
    tesseract-ocr \
    ocrmypdf \
    cron \
    curl \
    tzdata \
    && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && dpkg-reconfigure -f noninteractive tzdata && \
    rm -rf /var/lib/apt/lists/*

# Ensure python3 and python point to python3.10
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Upgrade pip
RUN python -m pip install --upgrade pip

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Setup cron job¬
COPY crontab.txt /etc/cron.d/uploader-cron
RUN chmod 0644 /etc/cron.d/uploader-cron && \
    touch /var/log/cron.log

# Start cron in foreground
CMD ["cron", "-f"]