# Deployment Guide

This guide covers deploying the Delta Exchange Trading Platform for 24/7 operation.

## Prerequisites

- Docker and Docker Compose installed
- PostgreSQL 15+ (or use containerized version)
- Redis 7+ (or use containerized version)
- System with at least 4GB RAM and 2 CPU cores
- Linux (systemd) or Windows (NSSM) for service management

## Quick Start

1. **Clone and configure:**
```bash
git clone <repository-url>
cd Crypto_Trading
cp .env.example .env
```

2. **Generate master key:**
```bash
openssl rand -hex 32
```
Add the output to `TRADE_MASTER_KEY` in `.env`

3. **Configure environment:**
Edit `.env` with your database credentials, API URLs, and other settings.

4. **Start services:**
```bash
docker-compose up -d
```

5. **Run migrations:**
```bash
docker-compose exec backend alembic upgrade head
```

6. **Verify:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Linux Deployment (systemd)

### 1. Install to /opt/trading-platform

```bash
sudo mkdir -p /opt/trading-platform
sudo cp -r . /opt/trading-platform/
cd /opt/trading-platform
sudo chown -R $USER:$USER /opt/trading-platform
```

### 2. Create systemd service

```bash
sudo cp deployment/systemd/trading-platform.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable trading-platform
sudo systemctl start trading-platform
```

### 3. Check status

```bash
sudo systemctl status trading-platform
docker-compose ps
```

### 4. View logs

```bash
sudo journalctl -u trading-platform -f
docker-compose logs -f
```

## Windows Deployment (NSSM)

### 1. Install NSSM

Download from https://nssm.cc/download and extract.

### 2. Create service

```powershell
cd C:\path\to\nssm\win64
.\nssm install TradingPlatform
```

In the NSSM GUI:
- **Path**: `docker-compose.exe`
- **Startup directory**: `D:\CryptoTrading\Crypto_Trading`
- **Arguments**: `-f docker-compose.yml up -d`

### 3. Start service

```powershell
.\nssm start TradingPlatform
```

### 4. View logs

```powershell
.\nssm status TradingPlatform
docker-compose logs -f
```

## Log Rotation

### Linux (logrotate)

1. Copy logrotate config:
```bash
sudo cp deployment/logrotate/trading-platform /etc/logrotate.d/
```

2. Test configuration:
```bash
sudo logrotate -d /etc/logrotate.d/trading-platform
```

### Windows

Use Windows Event Viewer or configure Docker logging driver limits in `docker-compose.yml`:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "5"
```

## Database Backups

### Automated backup script (Linux)

Create `/opt/trading-platform/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/trading-platform/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

docker-compose exec -T postgres pg_dump -U trading_user trading_db | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /opt/trading-platform/backup.sh
```

## Monitoring

### Health Checks

- Backend: `curl http://localhost:8000/health`
- Metrics: `curl http://localhost:8000/metrics`

### Prometheus Integration

The backend exposes Prometheus metrics at `/metrics`. Configure Prometheus to scrape this endpoint.

### Grafana Dashboard

Import the provided Grafana dashboard configuration (optional) for visualization.

## Updating

1. **Pull latest code:**
```bash
git pull
```

2. **Rebuild containers:**
```bash
docker-compose build
docker-compose up -d
```

3. **Run migrations:**
```bash
docker-compose exec backend alembic upgrade head
```

## Rollback

1. **Stop services:**
```bash
docker-compose down
```

2. **Checkout previous version:**
```bash
git checkout <previous-commit>
```

3. **Restart:**
```bash
docker-compose up -d
```

## Troubleshooting

### Services won't start

1. Check Docker is running: `docker ps`
2. Check ports are available: `netstat -tulpn | grep -E '3000|8000|5432|6379'`
3. Check logs: `docker-compose logs`

### Database connection errors

1. Verify PostgreSQL is running: `docker-compose ps postgres`
2. Check credentials in `.env`
3. Test connection: `docker-compose exec postgres psql -U trading_user -d trading_db`

### Worker not executing

1. Check worker logs: `docker-compose logs worker`
2. Verify profiles are enabled in database
3. Check Redis connection: `docker-compose exec redis redis-cli ping`

### API key encryption errors

1. Verify `TRADE_MASTER_KEY` is set correctly
2. Ensure key is 32-byte hex string
3. Check logs for encryption errors

## Security Checklist

- [ ] Change default passwords
- [ ] Set strong `TRADE_MASTER_KEY`
- [ ] Use HTTPS in production (reverse proxy)
- [ ] Restrict CORS origins
- [ ] Enable firewall rules
- [ ] Regular security updates
- [ ] Database backups encrypted
- [ ] API keys rotated regularly

## Production Recommendations

1. **Use reverse proxy (nginx/traefik)** for HTTPS
2. **Separate database** from application containers
3. **Use managed Redis** (AWS ElastiCache, etc.) for production
4. **Enable monitoring** (Prometheus + Grafana)
5. **Set up alerts** for critical errors
6. **Regular backups** with tested restore procedures
7. **Resource limits** in docker-compose.yml
8. **Network isolation** for containers

