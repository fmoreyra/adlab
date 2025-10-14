# Production Deployment Guide

This guide covers deploying the Laboratory System to a production server using Docker Compose with Nginx reverse proxy.

## Prerequisites

- Ubuntu Server 24.04 LTS (or similar)
- Docker and Docker Compose v2 installed
- Domain name pointed to your server
- Ports 80 and 443 accessible from internet

## Quick Start

### 1. Clone Repository

```bash
cd /opt
sudo mkdir laboratory-system
sudo chown $USER:$USER laboratory-system
cd laboratory-system
git clone <your-repo-url> .
```

### 2. Configure Environment

```bash
# Copy production environment template
cp .env.production.example .env

# Edit configuration
nano .env
```

**Important variables to change:**
- `SECRET_KEY` - Generate with: `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`
- `POSTGRES_PASSWORD` - Strong random password
- `ALLOWED_HOSTS` - Your domain name
- `DOMAIN_NAME` - Your domain name

### 3. Build and Start Services

```bash
# Build images
docker compose -f compose.yaml -f compose.production.yaml build

# Start database and redis
docker compose -f compose.yaml -f compose.production.yaml up -d postgres redis

# Wait a few seconds for database to be ready
sleep 10

# Run migrations
./run manage migrate

# Create superuser
./run manage createsuperuser

# Collect static files
./run manage collectstatic --no-input

# Start all services (except nginx - we'll add SSL first)
docker compose -f compose.yaml -f compose.production.yaml up -d web worker beat
```

### 4. Initialize SSL Certificates

```bash
# Initialize Let's Encrypt SSL
./bin/init-letsencrypt.sh your-domain.com admin@your-domain.com

# For testing (uses staging certificates):
# ./bin/init-letsencrypt.sh your-domain.com admin@your-domain.com 1
```

### 5. Verify Deployment

```bash
# Check all services are running
docker compose -f compose.yaml -f compose.production.yaml ps

# Test application
curl https://your-domain.com/up

# View logs
docker compose -f compose.yaml -f compose.production.yaml logs -f
```

## Updating the Application

Use the production deployment script:

```bash
./bin/deploy-production.sh
```

This script will:
1. Backup the database
2. Pull latest changes
3. Build new images
4. Run migrations
5. Restart services
6. Verify health

## Backup and Restore

### Manual Backup

```bash
# Create backup directory
mkdir -p backups

# Backup database
docker compose -f compose.yaml -f compose.production.yaml exec -T postgres \
  pg_dump -U lab_user laboratory_db | gzip > backups/backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore from Backup

```bash
# Stop services
docker compose -f compose.yaml -f compose.production.yaml stop web worker beat

# Restore database
gunzip -c backups/backup_YYYYMMDD_HHMMSS.sql.gz | \
  docker compose -f compose.yaml -f compose.production.yaml exec -T postgres \
  psql -U lab_user laboratory_db

# Start services
docker compose -f compose.yaml -f compose.production.yaml up -d
```

## Monitoring

### View Logs

```bash
# All services
docker compose -f compose.yaml -f compose.production.yaml logs -f

# Specific service
docker compose -f compose.yaml -f compose.production.yaml logs -f web
docker compose -f compose.yaml -f compose.production.yaml logs -f nginx

# Nginx access logs
docker compose -f compose.yaml -f compose.production.yaml exec nginx tail -f /var/log/nginx/laboratory-access.log
```

### Check Service Status

```bash
docker compose -f compose.yaml -f compose.production.yaml ps
```

### Resource Usage

```bash
docker stats
```

## Troubleshooting

### SSL Certificate Issues

```bash
# Check certificate
docker compose -f compose.yaml -f compose.production.yaml exec certbot certbot certificates

# Renew certificate manually
docker compose -f compose.yaml -f compose.production.yaml run --rm certbot certbot renew

# Reload Nginx
docker compose -f compose.yaml -f compose.production.yaml exec nginx nginx -s reload
```

### Service Not Starting

```bash
# Check logs
docker compose -f compose.yaml -f compose.production.yaml logs web

# Restart service
docker compose -f compose.yaml -f compose.production.yaml restart web

# Full restart
docker compose -f compose.yaml -f compose.production.yaml down
docker compose -f compose.yaml -f compose.production.yaml up -d
```

### Database Connection Issues

```bash
# Check database is running
docker compose -f compose.yaml -f compose.production.yaml ps postgres

# Test connection
docker compose -f compose.yaml -f compose.production.yaml exec postgres psql -U lab_user laboratory_db

# Check Django can connect
./run manage check --database default
```

## Security Checklist

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` generated
- [ ] Strong `POSTGRES_PASSWORD` set
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] SSL certificates installed and auto-renewing
- [ ] Firewall configured (ports 80, 443, 22 only)
- [ ] Regular backups scheduled
- [ ] Email SMTP configured (when ready)
- [ ] System updates applied regularly

## Next Steps

1. Configure automated backups (cron job)
2. Set up monitoring (optional: Grafana + Prometheus)
3. Configure email SMTP for production
4. Set up systemd service for auto-start on boot
5. Test disaster recovery procedures
