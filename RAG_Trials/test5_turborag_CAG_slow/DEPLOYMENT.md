# 🚀 Financial Advisor Suite - Docker Deployment Guide

Complete guide for deploying the Financial Advisor Suite with Docker in various environments.

## 📋 Quick Start

**Your system is already containerized!** Here's how to deploy it:

### 🔧 Current Setup (Already Working)
```bash
# You already have this running:
docker compose up -d

# Check status:
docker ps
```

**Current containers:**
- **Ollama** (AI Models): `ollama/ollama:latest` → Port 11434
- **Open WebUI** (Chat): `ghcr.io/open-webui/open-webui:latest` → Port 3000  
- **Financial Advisor** (Streamlit + API): Custom build → Ports 8501, 8502

## 🎯 Deployment Options

### 1. Development Deployment (Current)
```bash
# What you're already running
docker compose up -d

# Pull models
bash pull_models.sh
```

### 2. Production Deployment
```bash
# Use the production configuration
./deploy.sh -e production

# Or manually:
docker compose -f docker-compose.prod.yml up -d
```

### 3. Production with Nginx Proxy
```bash
# Deploy with reverse proxy
./deploy.sh -e production -p production -n

# Access via:
# http://localhost (Open WebUI)
# http://localhost/streamlit/ (Streamlit)
# http://localhost/api/knowledge/ (Knowledge Base API)
```

### 4. Cloud Deployment
```bash
# For AWS, GCP, Azure deployment
docker compose -f docker-compose.cloud.yml up -d
```

## 📦 Deployment Configurations

### 🔧 docker-compose.yml (Development)
- **Purpose**: Local development
- **Features**: Easy debugging, hot reload
- **Ports**: Direct access (3000, 8501, 8502, 11434)

### 🏭 docker-compose.prod.yml (Production)
- **Purpose**: Production deployment
- **Features**: Health checks, resource limits, restart policies
- **Security**: Read-only volumes, authentication enabled
- **Monitoring**: Health checks and resource constraints

### ☁️ docker-compose.cloud.yml (Cloud)
- **Purpose**: Cloud platforms (AWS, GCP, Azure)
- **Features**: Traefik labels, external load balancer support
- **Optional**: Redis, PostgreSQL, Prometheus, Grafana
- **Scaling**: Resource reservations and limits

### 🌐 Nginx Proxy
- **Purpose**: Single entry point for all services
- **Features**: SSL termination, path-based routing
- **Routes**:
  - `/` → Open WebUI
  - `/streamlit/` → Streamlit interface
  - `/api/knowledge/` → Knowledge Base API

## 🛠 Deployment Script

The `deploy.sh` script provides automated deployment:

```bash
# Basic deployment
./deploy.sh

# Production deployment
./deploy.sh -e production

# Production with nginx proxy
./deploy.sh -e production -p production -n

# Skip model downloading
./deploy.sh --no-models

# Help
./deploy.sh --help
```

## 🔧 Environment Configuration

### Development (.env)
```env
OLLAMA_BASE_URL=http://ollama:11434
WEBUI_AUTH=False
WEBUI_NAME=Financial Advisor Suite (Dev)
LOG_LEVEL=DEBUG
```

### Production (.env.production)
```env
WEBUI_AUTH=True
WEBUI_SECRET_KEY=your-secret-key-here
DEFAULT_USER_ROLE=user
STREAMLIT_SERVER_HEADLESS=true
LOG_LEVEL=INFO
```

## 📊 Resource Requirements

### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8GB (6GB for models + 2GB for services)
- **Disk**: 20GB
- **Network**: Stable internet for model downloads

### Recommended Production
- **CPU**: 8 cores
- **RAM**: 16GB
- **Disk**: 50GB SSD
- **Network**: 1Gbps

### Cloud Instance Recommendations
- **AWS**: t3.xlarge or m5.xlarge
- **GCP**: n2-standard-4 or e2-standard-4
- **Azure**: Standard_D4s_v3

## 🔐 Security Configuration

### Production Security Checklist
- ✅ Enable authentication (`WEBUI_AUTH=True`)
- ✅ Set strong secret keys
- ✅ Disable public signup (`ENABLE_SIGNUP=False`)
- ✅ Use read-only document mounts
- ✅ Configure SSL/TLS
- ✅ Set up firewall rules
- ✅ Regular security updates

### Nginx SSL Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # Include location blocks...
}
```

## 🌍 Cloud Platform Guides

### AWS Deployment
```bash
# EC2 instance setup
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Deploy
git clone <your-repo>
cd test5_turborag_CAG
./deploy.sh -e production
```

### Google Cloud Platform
```bash
# Create VM with Docker
gcloud compute instances create financial-advisor \
  --image-family=cos-stable \
  --image-project=cos-cloud \
  --machine-type=n2-standard-4 \
  --boot-disk-size=50GB

# SSH and deploy
gcloud compute ssh financial-advisor
git clone <your-repo>
cd test5_turborag_CAG
./deploy.sh -e production
```

### Azure Container Instances
```bash
# Create resource group
az group create --name financial-advisor --location eastus

# Deploy using docker-compose
az container create \
  --resource-group financial-advisor \
  --file docker-compose.cloud.yml
```

## 📈 Scaling and Monitoring

### Horizontal Scaling
```yaml
# docker-compose.scale.yml
services:
  financial_advisor:
    deploy:
      replicas: 3
    ports:
      - "8501-8503:8501"  # Multiple ports
      - "8502-8504:8502"
```

### Monitoring Stack
```bash
# Deploy with monitoring
docker compose -f docker-compose.cloud.yml --profile monitoring up -d

# Access Grafana: http://localhost:3000
# Access Prometheus: http://localhost:9090
```

### Health Checks
```bash
# Check all services
curl http://localhost/health

# Individual service checks
curl http://localhost:11434/api/version  # Ollama
curl http://localhost:3000/health        # Open WebUI
curl http://localhost:8501/_stcore/health # Streamlit
curl http://localhost:8502/              # Knowledge Base API
```

## 🔄 Backup and Recovery

### Data Volumes to Backup
```bash
# Create backups
docker volume ls | grep financial

# Backup volumes
docker run --rm -v shared_models:/data -v $(pwd):/backup alpine tar czf /backup/models.tar.gz -C /data .
docker run --rm -v openwebui_data:/data -v $(pwd):/backup alpine tar czf /backup/webui.tar.gz -C /data .
```

### Recovery Process
```bash
# Restore from backup
docker volume create shared_models
docker run --rm -v shared_models:/data -v $(pwd):/backup alpine tar xzf /backup/models.tar.gz -C /data
```

## 🚨 Troubleshooting

### Common Issues

**1. Out of Memory**
```bash
# Check memory usage
docker stats

# Reduce model size or increase RAM
# Edit pull_models.sh to use smaller models
```

**2. Port Conflicts**
```bash
# Check port usage
netstat -tlnp | grep :3000

# Change ports in docker-compose.yml
ports:
  - "3001:8080"  # Changed from 3000
```

**3. Models Not Loading**
```bash
# Check Ollama logs
docker logs test5_turborag_cag-ollama-1

# Manually pull models
docker exec -it test5_turborag_cag-ollama-1 ollama pull llama3.2:1b
```

**4. SSL Certificate Issues**
```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem -out ssl/cert.pem
```

### Log Collection
```bash
# Collect all logs
docker compose logs > deployment.log

# Service-specific logs
docker logs test5_turborag_cag-ollama-1 > ollama.log
docker logs test5_turborag_cag-open-webui-1 > webui.log
docker logs test5_turborag_cag-financial_advisor-1 > app.log
```

## 🎯 Performance Optimization

### Model Optimization
- Use quantized models (Q4, Q5)
- Implement model caching
- Configure model offloading

### Database Optimization
- Use external PostgreSQL for production
- Implement connection pooling
- Regular vacuum and analysis

### Caching Strategy
- Redis for session management
- NGINX caching for static assets
- Vector store caching

## 📞 Support and Maintenance

### Regular Maintenance Tasks
1. **Weekly**: Update container images
2. **Monthly**: Backup data volumes
3. **Quarterly**: Security audit and updates
4. **As needed**: Scale resources based on usage

### Update Process
```bash
# Update images
docker compose pull

# Recreate containers
docker compose up -d --force-recreate

# Verify health
./deploy.sh --no-models  # Runs health checks
```

---

## 🎉 Quick Deploy Commands

**Current Development:**
```bash
docker compose up -d && bash pull_models.sh
```

**Production Ready:**
```bash
./deploy.sh -e production
```

**Cloud Deployment:**
```bash
./deploy.sh -e production -p production -n
```

Your Financial Advisor Suite is now ready for any deployment scenario! 🚀