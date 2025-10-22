# Production Deployment Fixes Summary

## Overview
This document summarizes all the critical fixes made during the production deployment of the AdLab Laboratory Management System on October 20, 2025.

## Deployment Environment
- **Domain**: `adlab.moreyra.com.ar`
- **Server**: 147.93.7.60
- **SSL**: Let's Encrypt certificates
- **Web Server**: Nginx reverse proxy
- **Application**: Django with Docker Compose

---

## 🔧 Critical Fixes Applied

### 1. Dockerfile Build Issues
**Problem**: Docker build failing due to missing `run` script
```
ERROR: /bin/sh: 1: ../run: not found
```

**Root Cause**: The `run` script was removed from the repository but Dockerfile still referenced it.

**Solution**: Updated `Dockerfile` to use direct build commands:
```dockerfile
# Before (line 29-30):
RUN if [ "${NODE_ENV}" != "development" ]; then \
  ../run yarn:build:js && ../run yarn:build:css && ../run yarn:optimize:images; else mkdir -p /app/public; fi

# After:
RUN if [ "${NODE_ENV}" != "development" ]; then \
  node esbuild.config.mjs && \
  npx tailwindcss -i css/app.css -o ../public/css/app.css --minify && \
  node optimize-images.js; else mkdir -p /app/public; fi
```

**Files Modified**: `Dockerfile`

---

### 2. Django SSL Redirect Configuration
**Problem**: Django returning 502 Bad Gateway due to SSL redirect conflicts
```
SECURE_SSL_REDIRECT: True (hardcoded)
```

**Root Cause**: Django was hardcoded to redirect HTTP to HTTPS, but Nginx was making internal HTTP requests.

**Solution**: Updated Django settings to respect environment variable:
```python
# Before (line 236):
SECURE_SSL_REDIRECT = True

# After:
SECURE_SSL_REDIRECT = bool(strtobool(os.getenv("SECURE_SSL_REDIRECT", "true")))
```

**Environment Variable**: `SECURE_SSL_REDIRECT=False` in `.env`

**Files Modified**: `src/config/settings.py`

---

### 3. Nginx Upstream Configuration
**Problem**: Nginx returning 502 Bad Gateway
```
connect() failed (111: Connection refused) while connecting to upstream
```

**Root Cause**: Nginx upstream pointing to `web:8000` but actual container name was `laboratory-web-1`.

**Solution**: Updated Nginx configuration:
```nginx
# Before:
upstream django_app {
    server web:8000;
}

# After:
upstream django_app {
    server laboratory-web-1:8000;
}
```

**Files Modified**: `nginx/conf.d/laboratory.conf.template`

---

### 4. Static Files Serving (WhiteNoise)
**Problem**: 404 errors on static files (CSS, images, JS)
```
HTTP/2 400 on /static/css/app.css
```

**Root Cause**: WhiteNoise not configured to serve from correct location.

**Solution**: Updated WhiteNoise storage configuration:
```python
# Before:
"staticfiles": {
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
}

# After:
"staticfiles": {
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    "OPTIONS": {
        "location": "/public_collected",
        "base_url": "/static/",
    },
}
```

**Files Modified**: `src/config/settings.py`

---

### 5. SSL Certificate Volume Mounting
**Problem**: Let's Encrypt certificates not persisting after generation
```
certificates not saved due to read-only volume
```

**Root Cause**: Docker volume mounts were read-only for Certbot configuration.

**Solution**: Updated Docker Compose volume mounts:
```yaml
# Before:
- ./certbot/conf:/etc/letsencrypt:ro
- ./certbot/www:/var/www/certbot:ro

# After:
- ./certbot/conf:/etc/letsencrypt:rw
- ./certbot/www:/var/www/certbot:rw
```

**Files Modified**: `compose.production.yaml`

---

## 🚀 Deployment Commands Used

### Initial Deployment
```bash
# Pull latest code and deploy
ssh root@147.93.7.60 "cd /opt/laboratory-system && git pull origin main && docker compose down && docker compose up -d --build"
```

### SSL Certificate Generation
```bash
# Generate Let's Encrypt certificates
cd /opt/laboratory-system
docker stop laboratory-nginx
certbot certonly --standalone \
  -d adlab.moreyra.com.ar \
  --email facundo@moreyra.com.ar --agree-tos --no-eff-email \
  --config-dir certbot/conf --work-dir certbot/work --logs-dir certbot/logs
docker start laboratory-nginx
```

### Static Files Collection
```bash
# Collect static files
docker exec laboratory-web-1 python manage.py collectstatic --no-input --clear
```

---

## 🔍 Troubleshooting Commands

### Check Container Status
```bash
docker ps | grep -E "(web|nginx)"
```

### Check Django Logs
```bash
docker logs laboratory-web-1 --tail 20
```

### Check Nginx Logs
```bash
docker logs laboratory-nginx --tail 20
```

### Test Internal Connections
```bash
# Test Django health
docker exec laboratory-web-1 curl -I http://localhost:8000/up/

# Test Nginx to Django
docker exec laboratory-nginx wget -qO- http://laboratory-web-1:8000/up/
```

### Check SSL Certificates
```bash
# List certificates
certbot certificates --config-dir certbot/conf

# Test certificate
openssl x509 -in certbot/conf/live/adlab.moreyra.com.ar/fullchain.pem -noout -issuer -subject -dates
```

---

## 📋 Environment Variables

### Required in `.env` file:
```bash
SECRET_KEY=your-super-secret-key-here-change-this
DEBUG=False
ALLOWED_HOSTS=adlab.moreyra.com.ar,147.93.7.60,localhost,127.0.0.1,172.18.0.0/16
CSRF_TRUSTED_ORIGINS=https://adlab.moreyra.com.ar
SECURE_SSL_REDIRECT=False  # Nginx handles SSL redirect
```

---

## 🎯 Final Production Stack

- **Domain**: `https://adlab.moreyra.com.ar`
- **SSL**: Let's Encrypt certificates (auto-renewal)
- **Web Server**: Nginx 1.25.5 with HTTP/2
- **Application**: Django with Gunicorn
- **Database**: PostgreSQL 18.0
- **Cache**: Redis 8.2.2
- **Background Tasks**: Celery
- **Static Files**: WhiteNoise
- **Container Orchestration**: Docker Compose

---

## 🔄 Automatic Renewal Setup

SSL certificates are automatically renewed via:
- **Certbot container**: Runs every 12 hours
- **Cron job backup**: `30 2,14 * * * cd /opt/laboratory-system && certbot renew --quiet --config-dir certbot/conf --work-dir certbot/work --logs-dir certbot/logs && docker restart laboratory-nginx`

---

## 📝 Lessons Learned

1. **Always check container names** when configuring upstream servers
2. **Environment variables** should be respected in Django settings
3. **Volume permissions** are critical for certificate persistence
4. **Static file configuration** requires proper WhiteNoise setup
5. **Build scripts** should be updated when dependencies change

---

## 🚨 Common Issues to Watch

1. **Certificate expiration**: Monitor renewal logs
2. **Container name changes**: Update Nginx upstream if containers are recreated
3. **Static file 404s**: Check WhiteNoise configuration
4. **SSL redirect loops**: Ensure Django respects environment variables
5. **Volume permissions**: Verify read-write access for persistent data

---

*Last Updated: October 20, 2025*
*Deployment Status: ✅ Production Ready*
