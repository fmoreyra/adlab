# Production Deployment Guide

Complete guide for deploying the Laboratory Management System to a production server.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Deployment Process](#deployment-process)
- [SSL Configuration](#ssl-configuration)
- [Monitoring](#monitoring)
- [Backup and Restore](#backup-and-restore)
- [Rollback](#rollback)
- [Troubleshooting](#troubleshooting)
- [Security Checklist](#security-checklist)

## Prerequisites

### Server Requirements

**Minimum:**
- OS: Ubuntu 20.04+ or CentOS 8+
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB free space

**Recommended:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB+ free space

### Required Software

- Docker 20.10+ with Docker Compose v2
- Git 2.25+
- curl (for health checks)
- gzip (for backups)

### Network Requirements

- Domain name pointed to your server
- Ports 80 and 443 accessible from internet
- Port 22 for SSH access
- Stable internet connection

## Quick Start

This section provides a streamlined deployment process for production.

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

# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# Edit configuration
nano .env
```

**Critical variables to set:**

```bash
# Django Settings
SECRET_KEY=<generated-secret-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DOMAIN_NAME=yourdomain.com

# Database
POSTGRES_USER=lab_user
POSTGRES_PASSWORD=<strong-random-password>
POSTGRES_DB=laboratory_db

# Email (see Configuration Guide for SMTP details)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.yourdomain.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=<email-password>
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Security
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True

# Redis & Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
```

See [Environment Variables](../configuration/environment-variables.md) for complete reference.

### 3. Install Docker (if needed)

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Re-login for group changes to take effect
exit
# SSH back in
```

### 4. Build and Start Services

```bash
# Build images
docker compose -f compose.yaml -f compose.production.yaml build

# Start database and redis
docker compose -f compose.yaml -f compose.production.yaml up -d postgres redis

# Wait for database to be ready
sleep 10

# Run migrations
./run manage migrate

# Create superuser
./run manage createsuperuser

# Collect static files
./run manage collectstatic --no-input

# Start application services
docker compose -f compose.yaml -f compose.production.yaml up -d web worker beat
```

### 5. Initialize SSL Certificates

```bash
# Initialize Let's Encrypt SSL
./bin/init-letsencrypt.sh yourdomain.com admin@yourdomain.com

# For testing (uses Let's Encrypt staging):
# ./bin/init-letsencrypt.sh yourdomain.com admin@yourdomain.com 1
```

This will:
- Request SSL certificates from Let's Encrypt
- Configure Nginx with SSL
- Set up automatic certificate renewal

See [SSL Certificates](./ssl-certificates.md) for detailed SSL setup.

### 6. Verify Deployment

```bash
# Check all services are running
docker compose -f compose.yaml -f compose.production.yaml ps

# Test application health
curl https://yourdomain.com/up

# View logs
docker compose -f compose.yaml -f compose.production.yaml logs -f web
```

Expected output from health check:
```json
{"status": "ok", "database": "connected", "cache": "connected"}
```

## Detailed Setup

### Automated Setup (Recommended)

For fresh server setup, use the automated setup script:

```bash
# Download and run the setup script
curl -fsSL https://raw.githubusercontent.com/your-username/laboratory-system/main/bin/setup-server -o setup-server.sh
chmod +x setup-server.sh

# Run automated setup
./setup-server.sh --repo https://github.com/your-username/laboratory-system.git --domain yourdomain.com
```

**Setup script features:**
- ✅ Updates system packages
- ✅ Installs Docker and Docker Compose
- ✅ Configures firewall (UFW) and fail2ban
- ✅ Creates application directory
- ✅ Clones repository
- ✅ Sets up environment configuration
- ✅ Configures systemd service
- ✅ Sets up log rotation
- ✅ Configures automated backups
- ✅ Runs initial deployment

### Manual Setup

If you prefer manual setup or the automated script isn't suitable, follow the [Quick Start](#quick-start) section above for step-by-step manual instructions.

## Deployment Process

### Pre-Deployment Checklist

Before deploying, run the pre-deployment check script:

```bash
# Run comprehensive checks
./bin/pre-deploy-check
```

This verifies:
- ✅ Project directory structure
- ✅ Git repository status
- ✅ Environment configuration
- ✅ System resources (disk space, memory)
- ✅ Docker installation and status
- ✅ Database connectivity
- ✅ Redis connectivity
- ✅ Pending migrations
- ✅ Application health
- ✅ Security settings

### Deploy to Production

Use the deployment script for updates:

```bash
# Deploy latest changes
./bin/deploy-production.sh
```

The deployment script will:
1. 🔍 **Validate** environment and configuration
2. 💾 **Backup** current database automatically
3. 📥 **Pull** latest changes from git
4. 🏗️ **Build** new Docker images
5. 🔄 **Run** database migrations (if any)
6. 🚀 **Restart** services with zero downtime
7. ✅ **Verify** deployment health
8. 🧹 **Cleanup** old Docker resources

### Monitor Deployment

```bash
# Watch application logs in real-time
docker compose -f compose.yaml -f compose.production.yaml logs -f web

# Check all service statuses
docker compose -f compose.yaml -f compose.production.yaml ps

# Test application
curl https://yourdomain.com/up

# View recent errors
docker compose -f compose.yaml -f compose.production.yaml logs --tail=50 web | grep ERROR
```

## SSL Configuration

### Automatic SSL with Let's Encrypt

The system includes automated SSL certificate management:

```bash
# Initial setup
./bin/init-letsencrypt.sh yourdomain.com admin@yourdomain.com
```

### Certificate Renewal

Certificates automatically renew via cron job. To manually renew:

```bash
# Manual renewal
docker compose -f compose.yaml -f compose.production.yaml run --rm certbot certbot renew

# Reload Nginx
docker compose -f compose.yaml -f compose.production.yaml exec nginx nginx -s reload

# Check certificate status
docker compose -f compose.yaml -f compose.production.yaml exec certbot certbot certificates
```

See [SSL Certificates Guide](./ssl-certificates.md) for detailed SSL documentation.

## Monitoring

### View Logs

```bash
# All services
docker compose -f compose.yaml -f compose.production.yaml logs -f

# Specific service
docker compose -f compose.yaml -f compose.production.yaml logs -f web
docker compose -f compose.yaml -f compose.production.yaml logs -f nginx
docker compose -f compose.yaml -f compose.production.yaml logs -f worker

# Nginx access logs
docker compose -f compose.yaml -f compose.production.yaml exec nginx tail -f /var/log/nginx/laboratory-access.log

# Nginx error logs
docker compose -f compose.yaml -f compose.production.yaml exec nginx tail -f /var/log/nginx/laboratory-error.log
```

### Check Service Status

```bash
# Service status
docker compose -f compose.yaml -f compose.production.yaml ps

# Resource usage
docker stats

# Application health
curl https://yourdomain.com/up
```

### Automated Monitoring

Set up automated health checks:

```bash
# Check monitoring logs
tail -f /opt/laboratory-system/logs/monitor.log

# Run manual health check
/opt/laboratory-system/bin/monitor
```

See [Operations Guide](../operations/) for detailed monitoring procedures.

## Backup and Restore

### Automated Backups

The system includes automated backup scripts:

```bash
# Backups are stored in: /opt/laboratory-system/backups/
ls -lh /opt/laboratory-system/backups/

# Backup retention: 7 daily, 4 weekly, 3 monthly
```

### Manual Backup

```bash
# Create backup directory if needed
mkdir -p backups

# Backup database
./run db:dump
# Creates: backups/adlab_dump_YYYYMMDD_HHMMSS.sql

# Or using Docker directly:
docker compose -f compose.yaml -f compose.production.yaml exec -T postgres \
  pg_dump -U lab_user laboratory_db | gzip > backups/backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore from Backup

```bash
# Stop application services (keep database running)
docker compose -f compose.yaml -f compose.production.yaml stop web worker beat

# Restore database
gunzip -c backups/backup_YYYYMMDD_HHMMSS.sql.gz | \
  docker compose -f compose.yaml -f compose.production.yaml exec -T postgres \
  psql -U lab_user laboratory_db

# Start application services
docker compose -f compose.yaml -f compose.production.yaml up -d web worker beat
```

See [Backup & Restore Guide](../operations/backup-restore.md) for detailed backup procedures.

## Rollback

If deployment issues occur, use the rollback process:

### Quick Rollback

```bash
# Interactive rollback (recommended)
./bin/rollback
```

### Advanced Rollback Options

```bash
# List available backups
./bin/rollback --list

# Restore specific backup
./bin/rollback --backup db_backup_20241201_143022.sql.gz

# Rollback to specific git commit
./bin/rollback --commit abc1234

# Force rollback (skip confirmations - use with caution)
./bin/rollback --force
```

### Manual Rollback

```bash
# 1. Stop services
docker compose -f compose.yaml -f compose.production.yaml stop web worker beat

# 2. Revert code to previous commit
git reset --hard HEAD~1

# 3. Rebuild images
docker compose -f compose.yaml -f compose.production.yaml build

# 4. Restore database if needed
# (see Backup and Restore section)

# 5. Start services
docker compose -f compose.yaml -f compose.production.yaml up -d
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

# Test SSL configuration
curl -vI https://yourdomain.com
```

### Service Not Starting

```bash
# Check logs for specific service
docker compose -f compose.yaml -f compose.production.yaml logs web

# Check container status
docker compose -f compose.yaml -f compose.production.yaml ps

# Restart specific service
docker compose -f compose.yaml -f compose.production.yaml restart web

# Full restart (if needed)
docker compose -f compose.yaml -f compose.production.yaml down
docker compose -f compose.yaml -f compose.production.yaml up -d
```

### Database Connection Issues

```bash
# Check database is running
docker compose -f compose.yaml -f compose.production.yaml ps postgres

# Test connection from within container
docker compose -f compose.yaml -f compose.production.yaml exec postgres psql -U lab_user laboratory_db

# Check Django can connect
./run manage check --database default

# View database logs
docker compose -f compose.yaml -f compose.production.yaml logs postgres
```

### Static Files Not Loading

```bash
# Collect static files again
./run manage collectstatic --no-input

# Check Nginx configuration
docker compose -f compose.yaml -f compose.production.yaml exec nginx nginx -t

# Restart Nginx
docker compose -f compose.yaml -f compose.production.yaml restart nginx
```

See [Troubleshooting Guide](../operations/troubleshooting.md) for more issues and solutions.

## Security Checklist

Before going live, verify all security settings:

### Environment Security
- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` generated (50+ characters)
- [ ] Strong `POSTGRES_PASSWORD` set (20+ characters)
- [ ] `ALLOWED_HOSTS` configured correctly (no wildcards)
- [ ] `DOMAIN_NAME` matches your actual domain

### SSL/TLS Security
- [ ] SSL certificates installed and valid
- [ ] Auto-renewal configured (certbot cron job)
- [ ] `SESSION_COOKIE_SECURE=True`
- [ ] `CSRF_COOKIE_SECURE=True`
- [ ] `SECURE_SSL_REDIRECT=True`
- [ ] HTTPS working without certificate warnings

### Firewall Configuration
- [ ] Firewall enabled (UFW or similar)
- [ ] Only necessary ports open (80, 443, 22)
- [ ] SSH port secured or changed
- [ ] fail2ban configured for SSH protection

### Backup & Recovery
- [ ] Automated backups configured
- [ ] Backup restoration tested successfully
- [ ] Backups stored securely (offsite if possible)
- [ ] Retention policy defined and implemented

### Application Security
- [ ] Email SMTP configured (when ready)
- [ ] System updates applied regularly
- [ ] Docker images up to date
- [ ] Database access restricted
- [ ] Redis access restricted
- [ ] No sensitive data in logs

### Access Control
- [ ] Strong passwords for all admin accounts
- [ ] SSH key-based authentication enabled
- [ ] Sudo access restricted
- [ ] Application user permissions configured correctly

See [Security Audit Guide](../configuration/security-audit.md) for comprehensive security review.

## Post-Deployment Tasks

After successful deployment:

1. **Configure Automated Backups**
   ```bash
   # Set up daily backups via cron
   crontab -e
   # Add: 0 2 * * * /opt/laboratory-system/bin/backup-database
   ```

2. **Set Up Monitoring** (optional)
   - Configure Grafana + Prometheus
   - Set up log aggregation
   - Configure alerting

3. **Configure Email**
   - Test email sending: `./run manage sendtestemail admin@yourdomain.com`
   - Configure SMTP properly
   - See [Email Setup Guide](../configuration/email-setup.md)

4. **Set Up Systemd Service** (auto-start on boot)
   ```bash
   # Copy service file
   sudo cp /opt/laboratory-system/bin/laboratory-system.service /etc/systemd/system/

   # Enable service
   sudo systemctl enable laboratory-system
   sudo systemctl start laboratory-system
   ```

5. **Test Disaster Recovery**
   - Perform test backup
   - Perform test restore
   - Verify rollback procedure

6. **Document Your Setup**
   - Note any custom configurations
   - Document any deviations from this guide
   - Update team documentation

## Next Steps

- [Configure Email](../configuration/email-setup.md) - Set up SMTP for notifications
- [Operations Guide](../operations/) - Daily operations and maintenance
- [Troubleshooting](../operations/troubleshooting.md) - Common issues and solutions
- [Backup Procedures](../operations/backup-restore.md) - Detailed backup documentation

## Additional Resources

- [Nginx Setup Guide](./nginx-setup.md) - Detailed Nginx configuration
- [SSL Certificate Setup](./ssl-certificates.md) - SSL/TLS configuration
- [Server Connection](./server-connection.md) - SSH and remote access
- [Production Checklist](../operations/production-checklist.md) - Pre-launch verification

---

[← Back to Deployment Documentation](./README.md) | [Documentation Home](../README.md)
