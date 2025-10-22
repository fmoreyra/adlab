# Environment Variables Reference

Complete reference for all `.env` configuration options.

## Overview

The laboratory system uses environment variables for configuration. These are defined in the `.env` file at the project root.

**Environment files:**
- `.env.example` - Development template with sensible defaults
- `.env.production.example` - Production template with security settings
- `.env` - Your actual configuration (git-ignored, never commit!)

## Quick Start

```bash
# Development
cp .env.example .env

# Production
cp .env.production.example .env
# Then edit with production values
```

## Core Django Settings

### DEBUG

Controls Django debug mode.

```bash
# Development
DEBUG=true

# Production (MUST be false!)
DEBUG=false
```

**Impact:**
- `true`: Shows detailed error pages, enables debug toolbar
- `false`: Shows generic error pages, better performance

⚠️ **Never run production with DEBUG=true** - it exposes sensitive information!

### SECRET_KEY

Django secret key for cryptographic signing.

```bash
# Development (insecure, for dev only)
SECRET_KEY=insecure_key_for_dev

# Production (MUST be changed!)
SECRET_KEY=<your-generated-secret-key>
```

**Generate a secure key:**
```bash
./run secret
# Or:
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

⚠️ **Critical for production:**
- Must be kept secret
- Must be at least 50 characters
- Change from default value

### ALLOWED_HOSTS

Comma-separated list of allowed hostnames.

```bash
# Development (permissive)
ALLOWED_HOSTS=.localhost,127.0.0.1,[::1]

# Production (specific domains)
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Production with wildcard subdomain
ALLOWED_HOSTS=.yourdomain.com

# Multiple domains
ALLOWED_HOSTS=domain1.com,domain2.com,192.168.1.100
```

**Must include:**
- Your domain name(s)
- Server IP address (if accessing by IP)
- Load balancer hostname (if applicable)

## Database Settings

### POSTGRES_USER

PostgreSQL username.

```bash
# Development
POSTGRES_USER=adlab

# Production (can be different)
POSTGRES_USER=lab_user
```

### POSTGRES_PASSWORD

PostgreSQL password.

```bash
# Development (simple)
POSTGRES_PASSWORD=password

# Production (MUST be strong!)
POSTGRES_PASSWORD=<strong-random-password-20plus-chars>
```

⚠️ **Generate strong password:**
```bash
openssl rand -base64 24
```

### POSTGRES_DB

Database name.

```bash
# Development
POSTGRES_DB=adlab

# Production
POSTGRES_DB=laboratory_db
```

### POSTGRES_HOST

Database hostname.

```bash
# Docker Compose (default)
POSTGRES_HOST=postgres

# External database
POSTGRES_HOST=db.example.com
POSTGRES_HOST=192.168.1.50
```

### POSTGRES_PORT

Database port.

```bash
# Default PostgreSQL port
POSTGRES_PORT=5432

# Custom port (if needed)
POSTGRES_PORT=5433
```

## Redis Settings

### REDIS_URL

Redis connection URL.

```bash
# Docker Compose (default)
REDIS_URL=redis://redis:6379/0

# External Redis
REDIS_URL=redis://redis.example.com:6379/0

# With password
REDIS_URL=redis://:password@redis:6379/0

# Redis Sentinel
REDIS_URL=redis-sentinel://sentinel1:26379,sentinel2:26379/mymaster/0
```

## Celery Settings

### CELERY_BROKER_URL

Celery message broker URL (usually same as Redis).

```bash
# Docker Compose
CELERY_BROKER_URL=redis://redis:6379/0

# External
CELERY_BROKER_URL=redis://broker.example.com:6379/0
```

### CELERY_RESULT_BACKEND

Where Celery stores task results.

```bash
# Redis (recommended)
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Database (alternative)
CELERY_RESULT_BACKEND=django-db

# Disable (if not needed)
CELERY_RESULT_BACKEND=
```

## Email Settings

### EMAIL_BACKEND

Email backend to use.

```bash
# Production (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# Development (console)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Development (file)
EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend
EMAIL_FILE_PATH=/tmp/app-emails

# Testing (memory)
EMAIL_BACKEND=django.core.mail.backends.locmem.EmailBackend
```

### EMAIL_HOST

SMTP server hostname.

```bash
# Gmail
EMAIL_HOST=smtp.gmail.com

# Outlook/Microsoft 365
EMAIL_HOST=smtp.office365.com

# SendGrid
EMAIL_HOST=smtp.sendgrid.net

# Custom
EMAIL_HOST=smtp.yourdomain.com
```

### EMAIL_PORT

SMTP server port.

```bash
# TLS (recommended)
EMAIL_PORT=587

# SSL
EMAIL_PORT=465

# Unencrypted (not recommended)
EMAIL_PORT=25
```

### EMAIL_USE_TLS

Use TLS encryption (port 587).

```bash
# Recommended
EMAIL_USE_TLS=true

# If using SSL on port 465
EMAIL_USE_TLS=false
```

### EMAIL_USE_SSL

Use SSL encryption (port 465).

```bash
# If using SSL
EMAIL_USE_SSL=true

# If using TLS (port 587)
EMAIL_USE_SSL=false
```

⚠️ **Don't set both EMAIL_USE_TLS and EMAIL_USE_SSL to true!**

### EMAIL_HOST_USER

SMTP username.

```bash
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_USER=your-email@gmail.com
```

### EMAIL_HOST_PASSWORD

SMTP password or app-specific password.

```bash
EMAIL_HOST_PASSWORD=<your-email-password>

# Gmail: Use App Password, not regular password
# https://support.google.com/accounts/answer/185833
```

### DEFAULT_FROM_EMAIL

Default "From" address for emails.

```bash
DEFAULT_FROM_EMAIL=Laboratory System <noreply@yourdomain.com>
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

See [Email Setup Guide](./email-setup.md) for detailed email configuration.

## Security Settings

### SESSION_COOKIE_SECURE

Only send session cookie over HTTPS.

```bash
# Production (HTTPS enabled)
SESSION_COOKIE_SECURE=True

# Development (HTTP)
SESSION_COOKIE_SECURE=False
```

### CSRF_COOKIE_SECURE

Only send CSRF cookie over HTTPS.

```bash
# Production (HTTPS enabled)
CSRF_COOKIE_SECURE=True

# Development (HTTP)
CSRF_COOKIE_SECURE=False
```

### SECURE_SSL_REDIRECT

Redirect all HTTP requests to HTTPS.

```bash
# Production (after SSL is set up)
SECURE_SSL_REDIRECT=True

# Development or during SSL setup
SECURE_SSL_REDIRECT=False
```

⚠️ **Only enable after SSL certificates are working!**

### DOMAIN_NAME

Your domain name (used for SSL and email links).

```bash
# Production
DOMAIN_NAME=laboratory.yourdomain.com

# Development
DOMAIN_NAME=localhost
```

## Docker Settings

### COMPOSE_PROJECT_NAME

Docker Compose project name (prefix for containers).

```bash
COMPOSE_PROJECT_NAME=adlab
```

### COMPOSE_PROFILES

Which services to start.

```bash
# Development (all services)
COMPOSE_PROFILES=postgres,redis,assets,web,worker

# Production (no assets watcher)
COMPOSE_PROFILES=postgres,redis,web,worker

# Minimal (just app)
COMPOSE_PROFILES=postgres,redis,web
```

### Docker Port Forwards

Control which host ports services bind to.

```bash
# Web application
DOCKER_WEB_PORT_FORWARD=8000

# PostgreSQL
DOCKER_POSTGRES_PORT_FORWARD=5432

# Redis
DOCKER_REDIS_PORT_FORWARD=6379
```

**Port conflicts?** Change the host port:
```bash
DOCKER_WEB_PORT_FORWARD=8001
```

### UID and GID (Linux)

User/group IDs for file permissions.

```bash
# Check your IDs
id

# Set in .env (Linux only)
UID=1000
GID=1000
```

⚠️ **Linux users:** If you get permission errors, set these to match your user ID.

## Development Settings

### NODE_ENV

Node.js environment.

```bash
# Development
NODE_ENV=development

# Production
NODE_ENV=production
```

### PYTHONDONTWRITEBYTECODE

Prevent Python from writing `.pyc` files.

```bash
# Development (cleaner, recommended)
PYTHONDONTWRITEBYTECODE=true

# Production (slightly faster startup)
PYTHONDONTWRITEBYTECODE=false
```

### DOCKER_BUILDKIT

Enable Docker BuildKit for faster builds.

```bash
# Recommended
DOCKER_BUILDKIT=1
```

## Application-Specific Settings

### CELERY_TASK_ALWAYS_EAGER

Run Celery tasks synchronously (for testing).

```bash
# Testing (tasks run immediately)
CELERY_TASK_ALWAYS_EAGER=True

# Production (tasks run asynchronously)
CELERY_TASK_ALWAYS_EAGER=False
```

### RUNNING_TESTS / DJANGO_TESTING

Indicate test environment.

```bash
# During tests (set automatically by test runner)
RUNNING_TESTS=true
DJANGO_TESTING=true

# Normal operation
RUNNING_TESTS=false
DJANGO_TESTING=false
```

## Complete Examples

### Development `.env`

```bash
# Django
DEBUG=true
SECRET_KEY=insecure_key_for_dev
ALLOWED_HOSTS=.localhost,127.0.0.1,[::1]

# Database
POSTGRES_USER=adlab
POSTGRES_PASSWORD=password
POSTGRES_DB=adlab
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email (console)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Docker
COMPOSE_PROJECT_NAME=adlab
COMPOSE_PROFILES=postgres,redis,assets,web,worker
DOCKER_BUILDKIT=1
PYTHONDONTWRITEBYTECODE=true
```

### Production `.env`

```bash
# Django
DEBUG=False
SECRET_KEY=<generated-50-char-secret>
ALLOWED_HOSTS=laboratory.yourdomain.com,www.laboratory.yourdomain.com
DOMAIN_NAME=laboratory.yourdomain.com

# Database
POSTGRES_USER=lab_user
POSTGRES_PASSWORD=<strong-random-password>
POSTGRES_DB=laboratory_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=<app-password>
DEFAULT_FROM_EMAIL=Laboratory System <noreply@yourdomain.com>

# Security
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True

# Docker
COMPOSE_PROJECT_NAME=adlab
COMPOSE_PROFILES=postgres,redis,web,worker
DOCKER_BUILDKIT=1
```

## Validation Checklist

Before deploying to production, verify:

- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` is unique and strong (50+ chars)
- [ ] `ALLOWED_HOSTS` contains your domain(s)
- [ ] `POSTGRES_PASSWORD` is strong (20+ chars)
- [ ] `EMAIL_*` settings configured and tested
- [ ] `SESSION_COOKIE_SECURE=True`
- [ ] `CSRF_COOKIE_SECURE=True`
- [ ] `SECURE_SSL_REDIRECT=True` (after SSL works)
- [ ] No sensitive values committed to git

## Troubleshooting

### .env Not Loading

- Check file is named exactly `.env` (not `.env.txt`)
- Check file is in project root
- Restart Docker Compose: `docker compose down && docker compose up`

### Variables Not Taking Effect

- Restart services: `docker compose restart`
- Or full rebuild: `docker compose up --build`
- Check for typos in variable names

### Permission Denied (Linux)

- Set `UID` and `GID` to match your user (`id` command)
- Rebuild: `docker compose down && docker compose up --build`

## Related Documentation

- [Email Setup Guide](./email-setup.md) - Detailed email configuration
- [Security Audit](./security-audit.md) - Security best practices
- [Production Deployment](../deployment/production-deployment.md) - Production setup

---

[← Back to Configuration Documentation](./README.md) | [Documentation Home](../README.md)
