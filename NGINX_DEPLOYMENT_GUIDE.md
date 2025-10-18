# Nginx Production Deployment Guide

## Overview
This guide covers deploying nginx as a reverse proxy with SSL/TLS support for the Django application at `adlab.fmoreyra.com.ar`.

## Prerequisites
- Django application already running on port 8000
- Domain `adlab.fmoreyra.com.ar` DNS configured to point to your server
- Ports 80 and 443 open in firewall
- Docker and docker-compose installed

## Environment Variables Required

Create or update your `.env` file on the server with these production settings:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=adlab.fmoreyra.com.ar,.adlab.fmoreyra.com.ar
CSRF_TRUSTED_ORIGINS=https://adlab.fmoreyra.com.ar

# Database
POSTGRES_DB=adlab
POSTGRES_USER=adlab
POSTGRES_PASSWORD=your-secure-db-password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Email (configure for production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your-smtp-server.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=noreply@adlab.fmoreyra.com.ar
SERVER_EMAIL=server@adlab.fmoreyra.com.ar

# Docker Resource Limits (optional)
DOCKER_NGINX_CPUS=0.5
DOCKER_NGINX_MEMORY=256M
DOCKER_WEB_CPUS=1.0
DOCKER_WEB_MEMORY=512M
DOCKER_POSTGRES_CPUS=0.5
DOCKER_POSTGRES_MEMORY=256M
```

## Deployment Steps

### 1. Update Environment Variables
Ensure your `.env` file contains all the required variables listed above.

### 2. Deploy Nginx Container
```bash
# Start nginx with production compose
docker compose -f compose.yaml -f compose.production.yaml --profile nginx up -d nginx
```

### 3. Initialize Let's Encrypt SSL
**Important**: Only run this after DNS is configured and pointing to your server.

```bash
# Replace with your actual email address
./bin/init-letsencrypt.sh adlab.fmoreyra.com.ar your-email@example.com
```

### 4. Enable Certbot Auto-Renewal
```bash
docker compose -f compose.yaml -f compose.production.yaml --profile certbot up -d certbot
```

### 5. Verify Deployment
```bash
# Check all containers are running
docker compose ps

# Check nginx logs
docker compose logs nginx

# Test HTTP redirect
curl -I http://adlab.fmoreyra.com.ar

# Test HTTPS
curl -I https://adlab.fmoreyra.com.ar

# Test Django health check
curl https://adlab.fmoreyra.com.ar/up
```

## Security Features Enabled

- **HTTPS Redirect**: All HTTP traffic redirected to HTTPS
- **HSTS**: HTTP Strict Transport Security with 1-year max-age
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
- **Modern TLS**: TLS 1.2 and 1.3 only with secure cipher suites
- **SSL Certificate**: Let's Encrypt with automatic renewal

## Troubleshooting

### Nginx Won't Start
```bash
# Check nginx configuration syntax
docker compose -f compose.yaml -f compose.production.yaml exec nginx nginx -t

# Check nginx logs
docker compose logs nginx
```

### SSL Certificate Issues
```bash
# Check certificate status
docker compose -f compose.yaml -f compose.production.yaml exec certbot certbot certificates

# Test certificate renewal
docker compose -f compose.yaml -f compose.production.yaml exec certbot certbot renew --dry-run
```

### Django Not Accessible
```bash
# Check if Django container is running
docker compose ps web

# Check Django logs
docker compose logs web

# Test internal connectivity
docker compose -f compose.yaml -f compose.production.yaml exec nginx wget -qO- http://web:8000/up
```

## Rollback Plan

If you need to rollback:

```bash
# Stop nginx (Django will still be accessible on port 8000)
docker compose -f compose.yaml -f compose.production.yaml stop nginx

# Fix issues, then restart
docker compose -f compose.yaml -f compose.production.yaml start nginx
```

## Monitoring

### Log Locations
- Nginx access logs: `docker compose logs nginx`
- Nginx error logs: `docker compose logs nginx`
- Django logs: `docker compose logs web`
- SSL renewal logs: `docker compose logs certbot`

### Health Checks
- Nginx health: `curl -I https://adlab.fmoreyra.com.ar/up`
- SSL rating: https://www.ssllabs.com/ssltest/analyze.html?d=adlab.fmoreyra.com.ar

## Important Notes

1. **DNS Configuration**: Ensure `adlab.fmoreyra.com.ar` A record points to your server IP before running SSL setup
2. **Rate Limits**: Let's Encrypt has rate limits (5 failures/hour, 50 certificates/domain/week)
3. **Certificate Renewal**: Automatic via certbot container running every 12 hours
4. **Backup**: Always backup your database before major deployments
5. **Testing**: Use Let's Encrypt staging environment for testing: `./bin/init-letsencrypt.sh adlab.fmoreyra.com.ar your-email@example.com 1`

## Support

If you encounter issues:
1. Check the logs using the commands above
2. Verify all environment variables are set correctly
3. Ensure DNS is properly configured
4. Check firewall settings for ports 80 and 443
5. Review the troubleshooting section above
