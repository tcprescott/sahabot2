# Deployment Guide

Complete guide for deploying SahaBot2 to development, staging, and production environments.

**Last Updated**: November 4, 2025  
**Scope**: Setup, deployment procedures, and operational guidelines

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Staging Deployment](#staging-deployment)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Systemd Service](#systemd-service)
- [Reverse Proxy Setup](#reverse-proxy-setup)
- [SSL/HTTPS Configuration](#ssltls-configuration)
- [Database Management](#database-management)
- [Health Checks & Monitoring](#health-checks--monitoring)
- [Scaling Considerations](#scaling-considerations)
- [Backup & Recovery](#backup--recovery)
- [Deployment Checklist](#deployment-checklist)

---

## Overview

SahaBot2 is a **multi-tier application** with:
- **Backend**: FastAPI + NiceGUI server (Python)
- **Database**: MySQL with Tortoise ORM
- **Bot**: Discord.py bot (embedded in main process)
- **External Services**: Discord API, RaceTime.gg, ALTTPR API

### Deployment Topology

```
Users/Discord
     ↓
[Reverse Proxy: nginx/Apache]  ← SSL/TLS termination
     ↓
[SahaBot2 Application]  ← FastAPI + NiceGUI
     ↓
[MySQL Database]  ← Tortoise ORM
     ↓
[External APIs]  ← Discord, RaceTime, ALTTPR
```

### Environment Progression

```
Development (localhost:8080)
    ↓
Staging (staging.example.com)
    ↓
Production (example.com)
```

---

## Prerequisites

### System Requirements

**Minimum**:
- CPU: 2 cores
- RAM: 2GB
- Disk: 20GB
- Network: 10 Mbps

**Recommended**:
- CPU: 4+ cores
- RAM: 4GB+
- Disk: 50GB SSD
- Network: 100+ Mbps

### Software Requirements

```bash
# Python 3.11+
python --version
# Python 3.11.0

# Poetry (Python package manager)
poetry --version
# Poetry (version 1.7.0 or higher)

# MySQL 8.0+
mysql --version
# mysql  Ver 8.0.35

# Git (for cloning/updates)
git --version
# git version 2.42.0

# Optional: Docker & Docker Compose
docker --version
docker-compose --version
```

### System Permissions

**Non-root user recommended**:
```bash
# Create dedicated user
sudo useradd -m -s /bin/bash sahabot
sudo usermod -aG sudo sahabot

# Run as user
sudo su - sahabot
```

### Firewall Rules

**Inbound ports to open**:
- **80** (HTTP - redirect to HTTPS)
- **443** (HTTPS - main application)
- **3306** (MySQL - internal only, not exposed)

**Example with ufw**:
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 3306/tcp from 127.0.0.1  # MySQL local only
sudo ufw enable
```

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/tcprescott/sahabot2.git
cd sahabot2
```

### 2. Install Dependencies

```bash
# Using Poetry
poetry install

# Or with Python venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Setup Local Database

```bash
# Start MySQL (if not running)
brew services start mysql  # macOS
sudo service mysql start   # Ubuntu/Linux

# Create database
mysql -u root
> CREATE DATABASE sahabot2;
> CREATE USER 'sahabot2'@'localhost' IDENTIFIED BY 'devpassword';
> GRANT ALL PRIVILEGES ON sahabot2.* TO 'sahabot2'@'localhost';
> FLUSH PRIVILEGES;
> EXIT;
```

### 4. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit with your values
nano .env
# Set:
# DB_PASSWORD=devpassword
# DISCORD_CLIENT_ID=...
# DISCORD_BOT_TOKEN=...
# SECRET_KEY=dev_secret_key
```

### 5. Initialize Database

```bash
# Create schema and run migrations
poetry run aerich init-db

# Or if already initialized
poetry run aerich upgrade
```

### 6. Run Application

```bash
# Development mode (auto-reload, verbose output)
./start.sh dev

# Or directly
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8080

# Access at http://localhost:8080
```

### 7. Verify Setup

```bash
# Health check
curl http://localhost:8080/health

# Expected response
{"status": "ok", "timestamp": "2025-11-04T..."}
```

---

## Staging Deployment

### 1. Server Setup

**On staging server**:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv git mysql-server nginx curl

# Create application directory
sudo mkdir -p /opt/sahabot2
sudo chown sahabot:sahabot /opt/sahabot2

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### 2. Clone and Prepare Application

```bash
cd /opt/sahabot2
git clone https://github.com/tcprescott/sahabot2.git .

# Install dependencies
poetry install --no-dev

# Create .env for staging
nano .env
# Copy staging profile from ENVIRONMENT_VARIABLES.md
```

### 3. Database Setup

```bash
# Create MySQL user
mysql -u root -p
> CREATE DATABASE sahabot2_staging;
> CREATE USER 'sahabot_staging'@'localhost' IDENTIFIED BY 'strong_password_here';
> GRANT ALL PRIVILEGES ON sahabot2_staging.* TO 'sahabot_staging'@'localhost';
> FLUSH PRIVILEGES;
> EXIT;

# Initialize database
poetry run aerich init-db
poetry run aerich upgrade
```

### 4. Configure Systemd Service

> **Note**: A production-ready systemd service unit file is available as [`sahabot2.service`](../../sahabot2.service) in the repository root. For staging, you can copy and modify it, or use the simplified version below.

**File**: `/etc/systemd/system/sahabot2-staging.service`

```ini
[Unit]
Description=SahaBot2 Staging Application
After=network.target mysql.service

[Service]
Type=notify
User=sahabot
WorkingDirectory=/opt/sahabot2
Environment="PATH=/home/sahabot/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/sahabot/.local/bin/poetry run uvicorn main:app --host 127.0.0.1 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable sahabot2-staging

# Start service
sudo systemctl start sahabot2-staging

# Check status
sudo systemctl status sahabot2-staging

# View logs
sudo journalctl -u sahabot2-staging -f
```

### 6. Configure Nginx Reverse Proxy

> **Note**: A comprehensive sample Nginx configuration is available in the repository root as [`nginx.conf.sample`](../../nginx.conf.sample). The configuration below is a simplified version for staging. For production deployment with all features (rate limiting, security headers, static file serving, etc.), see the sample configuration file or the production configuration in section 8 below.

**File**: `/etc/nginx/sites-available/staging.sahabot2`

```nginx
upstream sahabot2_staging {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name staging.example.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name staging.example.com;
    
    ssl_certificate /etc/letsencrypt/live/staging.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging.example.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Logging
    access_log /var/log/nginx/staging.access.log;
    error_log /var/log/nginx/staging.error.log;
    
    # Proxy settings
    location / {
        proxy_pass http://sahabot2_staging;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 7. Enable Nginx Site

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/staging.sahabot2 \
           /etc/nginx/sites-enabled/staging.sahabot2

# Test Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 8. Test Deployment

```bash
# Health check
curl https://staging.example.com/health

# Expected response
{"status": "ok"}
```

---

## Production Deployment

### 1. Pre-Deployment Checklist

- [ ] Server resources verified (CPU, RAM, disk)
- [ ] Database backup exists
- [ ] SSL certificate acquired (Let's Encrypt)
- [ ] DNS records updated
- [ ] Firewall rules configured
- [ ] Monitoring/alerting setup
- [ ] Backup strategy planned

### 2. Production Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv git mysql-server nginx \
                    certbot python3-certbot-nginx curl wget htop

# Create application directory
sudo mkdir -p /opt/sahabot2-prod
sudo chown sahabot:sahabot /opt/sahabot2-prod

# Install Poetry as sahabot user
sudo su - sahabot
curl -sSL https://install.python-poetry.org | python3 -
exit
```

### 3. Deploy Application

```bash
cd /opt/sahabot2-prod
git clone https://github.com/tcprescott/sahabot2.git .

# Install with production flags
poetry install --no-dev --no-interaction

# Create production .env
nano .env
# Copy production profile from ENVIRONMENT_VARIABLES.md
```

### 4. Production Database Setup

```bash
# Create production MySQL instance
mysql -u root -p
> CREATE DATABASE sahabot2_prod;
> CREATE USER 'sahabot_prod'@'localhost' IDENTIFIED BY 'very_strong_password_min_20_chars';
> GRANT ALL PRIVILEGES ON sahabot2_prod.* TO 'sahabot_prod'@'localhost';
> FLUSH PRIVILEGES;

# Create backup user (read-only)
> CREATE USER 'sahabot_backup'@'localhost' IDENTIFIED BY 'backup_password';
> GRANT SELECT, LOCK TABLES ON sahabot2_prod.* TO 'sahabot_backup'@'localhost';
> FLUSH PRIVILEGES;
> EXIT;

# Initialize database
poetry run aerich init-db
poetry run aerich upgrade
```

### 5. Production Systemd Service

> **Note**: A production-ready systemd service unit file is available in the repository root as [`sahabot2.service`](../../sahabot2.service). This file includes comprehensive documentation, security hardening, and multiple configuration options. Copy it to `/etc/systemd/system/` and customize as needed.

**File**: `/etc/systemd/system/sahabot2.service`

```ini
[Unit]
Description=SahaBot2 Production Application
After=network.target mysql.service
Wants=sahabot2.timer

[Service]
Type=notify
User=sahabot
WorkingDirectory=/opt/sahabot2-prod
Environment="PATH=/home/sahabot/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="ENVIRONMENT=production"
Environment="DEBUG=false"

# Use gunicorn for production (multi-worker)
ExecStart=/home/sahabot/.local/bin/poetry run gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8080 \
    --access-logfile /var/log/sahabot2/access.log \
    --error-logfile /var/log/sahabot2/error.log \
    --log-level info \
    main:app

# Auto-restart
Restart=always
RestartSec=30
StartLimitInterval=600
StartLimitBurst=3

# Security
PrivateTmp=yes
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes

[Install]
WantedBy=multi-user.target
```

### 6. Log Directory Setup

```bash
# Create log directory
sudo mkdir -p /var/log/sahabot2
sudo chown sahabot:sahabot /var/log/sahabot2
sudo chmod 755 /var/log/sahabot2

# Logrotate configuration
sudo nano /etc/logrotate.d/sahabot2
```

**Content**:
```
/var/log/sahabot2/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 sahabot sahabot
    sharedscripts
    postrotate
        systemctl reload sahabot2 > /dev/null 2>&1 || true
    endscript
}
```

### 7. Enable and Start Production Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable sahabot2
sudo systemctl start sahabot2
sudo systemctl status sahabot2

# Follow logs
sudo journalctl -u sahabot2 -f
```

### 8. Production Nginx Configuration

> **Note**: A comprehensive, production-ready sample Nginx configuration is available in the repository root as [`nginx.conf.sample`](../../nginx.conf.sample). This sample includes all recommended settings for production deployment including WebSocket support, rate limiting, security headers, static file serving, gzip compression, and more. You can copy this file directly to your server and customize it for your domain.

**File**: `/etc/nginx/sites-available/sahabot2`

```nginx
upstream sahabot2 {
    # Multiple workers for load distribution
    server 127.0.0.1:8080 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;

server {
    listen 80;
    server_name example.com www.example.com;
    
    # Redirect all HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;
    
    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5:!SHA1;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS header
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Logging
    access_log /var/log/nginx/access.log combined buffer=32k flush=5s;
    error_log /var/log/nginx/error.log warn;
    
    # Client max body size for uploads
    client_max_body_size 100M;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_types text/plain text/css text/javascript application/json;
    
    # Rate limiting for API
    location /api/ {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://sahabot2;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Main application
    location / {
        limit_req zone=general burst=20 nodelay;
        proxy_pass http://sahabot2;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files (if served by Nginx)
    location /static/ {
        alias /opt/sahabot2-prod/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 9. Enable Production Nginx

```bash
sudo ln -s /etc/nginx/sites-available/sahabot2 \
           /etc/nginx/sites-enabled/sahabot2

sudo nginx -t
sudo systemctl reload nginx
```

### 10. SSL Certificate (Let's Encrypt)

```bash
# Generate certificate
sudo certbot certonly --nginx -d example.com -d www.example.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Test renewal
sudo certbot renew --dry-run
```

---

## Docker Deployment

### Dockerfile

**File**: `Dockerfile`

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /tmp
RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --output requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl mysql-client && rm -rf /var/lib/apt/lists/*

COPY --from=builder /tmp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Docker Compose

**File**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: sahabot2-db
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME}
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"
    networks:
      - sahabot2-network

  sahabot2:
    build: .
    container_name: sahabot2-app
    depends_on:
      - mysql
    environment:
      DB_HOST: mysql
      DB_PORT: 3306
      DB_USER: ${DB_USER}
      DB_PASSWORD: ${DB_PASSWORD}
      DB_NAME: ${DB_NAME}
      DISCORD_CLIENT_ID: ${DISCORD_CLIENT_ID}
      DISCORD_CLIENT_SECRET: ${DISCORD_CLIENT_SECRET}
      DISCORD_BOT_TOKEN: ${DISCORD_BOT_TOKEN}
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: ${ENVIRONMENT}
      BASE_URL: ${BASE_URL}
    ports:
      - "8080:8080"
    networks:
      - sahabot2-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  mysql_data:

networks:
  sahabot2-network:
    driver: bridge
```

### Docker Deployment

```bash
# Create environment file
nano .env.docker
# Copy relevant variables

# Build and start
docker-compose up -d

# Initialize database
docker-compose exec sahabot2 poetry run aerich init-db

# View logs
docker-compose logs -f sahabot2

# Stop
docker-compose down
```

---

## Systemd Service

> **Quick Start**: A production-ready systemd service unit file is available at [`sahabot2.service`](../../sahabot2.service) in the repository root. This file includes comprehensive documentation, security hardening options, and multiple configuration alternatives. Copy it to `/etc/systemd/system/` and follow the installation instructions in the file header.

### Service Management

```bash
# Start service
sudo systemctl start sahabot2

# Stop service
sudo systemctl stop sahabot2

# Restart service
sudo systemctl restart sahabot2

# Check status
sudo systemctl status sahabot2

# Enable on boot
sudo systemctl enable sahabot2

# Disable from boot
sudo systemctl disable sahabot2

# View logs
sudo journalctl -u sahabot2 -f

# Last 50 lines of logs
sudo journalctl -u sahabot2 -n 50
```

### Service Troubleshooting

```bash
# Check if service is running
systemctl is-active sahabot2

# Check if enabled
systemctl is-enabled sahabot2

# Check service status details
systemctl show sahabot2

# Reload systemd if config changed
sudo systemctl daemon-reload
```

---

## Reverse Proxy Setup

> **Quick Start**: A comprehensive sample Nginx configuration file is available at [`nginx.conf.sample`](../../nginx.conf.sample) in the repository root. This file includes all the settings mentioned in this section and more. Copy it to `/etc/nginx/sites-available/` and customize for your domain.

### Nginx Configuration Tips

**WebSocket Support** (required for NiceGUI):
```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

**Performance Tuning**:
```nginx
# Connection pooling
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=app_cache:10m max_size=1g;

# Gzip compression
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1000;
```

**Security Headers**:
```nginx
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

---

## SSL/TLS Configuration

### Let's Encrypt Setup

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d example.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Manual Certificate (Non-Let's Encrypt)

```bash
# Generate private key
openssl genrsa -out example.com.key 2048

# Generate CSR
openssl req -new -key example.com.key -out example.com.csr

# Get certificate from CA and place at example.com.crt

# Update Nginx
ssl_certificate /path/to/example.com.crt;
ssl_certificate_key /path/to/example.com.key;
```

### SSL Configuration Best Practices

```nginx
# Modern SSL settings
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

# HSTS
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
```

---

## Database Management

### Backup Strategy

**Daily backups**:
```bash
#!/bin/bash
# backup-sahabot2.sh

BACKUP_DIR="/backups/sahabot2"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/sahabot2_$DATE.sql.gz"

mkdir -p "$BACKUP_DIR"

mysqldump -u sahabot_backup -p"${BACKUP_PASSWORD}" \
          --single-transaction --quick \
          sahabot2_prod | gzip > "$BACKUP_FILE"

# Keep last 30 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

**Cron job**:
```bash
# Run daily at 2 AM
0 2 * * * /usr/local/bin/backup-sahabot2.sh >> /var/log/backup.log 2>&1
```

### Restore from Backup

```bash
# List backups
ls -lh /backups/sahabot2/

# Restore
gunzip < /backups/sahabot2/sahabot2_20251104_000000.sql.gz | \
  mysql -u root -p sahabot2_prod

# Or restore specific table
gunzip < backup.sql.gz | mysql -u root -p -e "USE sahabot2_prod; SOURCE /dev/stdin;"
```

### Database Maintenance

```bash
# Optimize tables
mysql -u root -p -e "USE sahabot2_prod; OPTIMIZE TABLE \`user\`, tournament, async_tournament;"

# Analyze tables
mysql -u root -p -e "USE sahabot2_prod; ANALYZE TABLE \`user\`, tournament, async_tournament;"

# Check table integrity
mysqlcheck -u root -p sahabot2_prod
```

---

## Health Checks & Monitoring

### Application Health Endpoint

```bash
# Should always be available (no auth required)
curl https://example.com/health

# Response
{"status": "ok", "timestamp": "2025-11-04T12:34:56Z"}
```

### Monitoring Setup

**Prometheus metrics** (if available):
```bash
curl https://example.com/metrics
```

**Systemd monitoring**:
```bash
# Alert on service failure
sudo systemctl enable sahabot2
sudo systemctl status sahabot2

# Or use monit/supervisor for more advanced monitoring
```

### Log Monitoring

```bash
# Real-time monitoring
tail -f /var/log/sahabot2/error.log

# Error rate
grep "ERROR" /var/log/sahabot2/error.log | wc -l

# Database connection issues
grep "database\|connection" /var/log/sahabot2/error.log
```

---

## Scaling Considerations

### Horizontal Scaling

**Multiple Application Instances**:
```nginx
upstream sahabot2_cluster {
    server 127.0.0.1:8080;
    server 127.0.0.1:8081;
    server 127.0.0.1:8082;
    server 127.0.0.1:8083;
}

server {
    location / {
        proxy_pass http://sahabot2_cluster;
        # Load balancing method
        # Default: round-robin
        # sticky: ip_hash;
    }
}
```

### Database Scaling

**Connection pooling**:
- Use PgBouncer or ProxySQL
- Tortoise ORM connection pool configuration

**Read replicas** (for large deployments):
- Set up MySQL replication
- Route read-heavy operations to replicas
- Keep writes to primary

### Caching Layer

**Redis for session/cache**:
```python
# Configure in config.py
CACHE_BACKEND=redis://localhost:6379/0
```

---

## Backup & Recovery

### Pre-Deployment Backup

```bash
# Full database backup before deployment
mysqldump -u root -p sahabot2_prod > pre-deploy-backup.sql

# Application code backup
git tag pre-deployment-$(date +%s)
git push origin --tags
```

### Disaster Recovery

**Quick checklist**:
1. Stop application: `sudo systemctl stop sahabot2`
2. Backup current database: `mysqldump ... > latest-backup.sql`
3. Restore from backup: `mysql < backup.sql`
4. Check data integrity
5. Restart application: `sudo systemctl start sahabot2`
6. Verify health: `curl https://example.com/health`

### Database Recovery from Snapshot

```bash
# If using cloud provider snapshots (AWS, GCP, etc.)
# 1. Create new database from snapshot
# 2. Update connection parameters
# 3. Restart application
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Code changes tested locally
- [ ] Database migrations tested
- [ ] Environment variables prepared
- [ ] SSL certificate acquired
- [ ] DNS records ready
- [ ] Backup created
- [ ] Monitoring configured
- [ ] Rollback plan documented

### Deployment

- [ ] Pull latest code: `git pull origin main`
- [ ] Install dependencies: `poetry install --no-dev`
- [ ] Run migrations: `poetry run aerich upgrade`
- [ ] Update environment variables: `nano .env`
- [ ] Restart service: `sudo systemctl restart sahabot2`
- [ ] Verify health: `curl https://example.com/health`
- [ ] Check logs: `sudo journalctl -u sahabot2 -f`
- [ ] Test critical features
- [ ] Notify team of deployment

### Post-Deployment

- [ ] Monitor error logs for issues
- [ ] Check database performance
- [ ] Verify Discord bot functionality
- [ ] Test API endpoints
- [ ] Check UI responsiveness
- [ ] Monitor resource usage (CPU, RAM, disk)
- [ ] Verify backups completed
- [ ] Document any issues
- [ ] Plan next deployment

### Rollback Procedure

```bash
# If deployment fails
sudo systemctl stop sahabot2

# Restore previous code
git revert HEAD
git pull

# Restore previous database (if needed)
mysql sahabot2_prod < backup-before-deploy.sql

# Restart
sudo systemctl start sahabot2

# Verify
curl https://example.com/health
```

---

## Troubleshooting Deployments

### Service Won't Start

```bash
# Check logs
sudo journalctl -u sahabot2 -n 50

# Check configuration
sudo systemctl status sahabot2

# Try starting manually to see errors
/home/sahabot/.local/bin/poetry run uvicorn main:app
```

### Database Connection Issues

See [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md#database-issues)

### Performance Problems

See [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md#performance-issues)

### Nginx Proxy Issues

```bash
# Test config
sudo nginx -t

# Check logs
sudo tail -f /var/log/nginx/error.log

# Reload
sudo systemctl reload nginx
```

---

## See Also

- [ENVIRONMENT_VARIABLES.md](../reference/ENVIRONMENT_VARIABLES.md) - Configuration reference
- [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md) - Common issues and debugging
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- Systemd documentation: https://systemd.io
- Nginx documentation: https://nginx.org/en/docs/
- Let's Encrypt: https://letsencrypt.org/
- MySQL documentation: https://dev.mysql.com/doc/

---

**Last Updated**: November 4, 2025
