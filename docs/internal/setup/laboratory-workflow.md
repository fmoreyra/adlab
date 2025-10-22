# Laboratory System Setup

## Overview

This is the Laboratory Pathology Management System based on the [docker-django-example](https://github.com/nickjj/docker-django-example) template.

## Services Configuration

### Core Services

1. **PostgreSQL 16** (`postgres`)
   - Database for the laboratory system
   - User: `lab_user`
   - Password: `lab_password_dev` (development)
   - Port: 5432

2. **Redis 7** (`redis`)
   - Used for:
     - Session storage
     - Celery message broker
     - Cache backend
   - Port: 6379

3. **Django Web** (`web`)
   - Main Django application
   - Port: 8000
   - Uses Gunicorn in production
   - Hot-reload enabled in development

4. **Celery Worker** (`worker`)
   - Handles async tasks:
     - Email notifications
     - PDF generation
     - Report exports
     - Data processing

5. **Celery Beat** (`beat`) ⭐ NEW
   - Scheduled task executor
   - Use cases:
     - Daily backup tasks
     - Periodic report generation
     - Reminder notifications
     - System health checks

6. **Asset Builders** (`js`, `css`)
   - Build JavaScript and CSS assets
   - Uses esbuild and Tailwind CSS

## Quick Start

### 1. Initial Setup

```bash
# Already done:
# - Cloned repository
# - Copied .env file
# - Updated project name and database credentials
# - Added Celery Beat service

# Install dependencies (builds the Docker image)
docker compose build
```

### 2. Start Services

```bash
# Start all services
docker compose up

# Or start in detached mode
docker compose up -d

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f web
docker compose logs -f worker
docker compose logs -f beat
```

### 3. Database Setup

```bash
# Create database migrations
./run manage makemigrations

# Apply migrations
./run manage migrate

# Create superuser
./run manage createsuperuser
```

### 4. Access the Application

- **Main App:** http://localhost:8000/
- **Django Admin:** http://localhost:8000/admin/

## Development Workflow

### Run Management Commands

```bash
# General format
./run manage <command>

# Examples
./run manage shell
./run manage dbshell
./run manage showmigrations
```

### Run Tests

```bash
# Run all tests
./run manage test

# Run quality checks
./run quality
```

### Access Services

```bash
# Django shell
./run manage shell

# PostgreSQL shell
./run manage dbshell

# Access Python container
docker compose exec web bash

# Access database directly
docker compose exec postgres psql -U lab_user
```

## Services for Laboratory System

### Required Services (All Running)

- ✅ **postgres** - Database
- ✅ **redis** - Cache & message broker
- ✅ **web** - Django application
- ✅ **worker** - Celery worker for async tasks
- ✅ **beat** - Celery beat for scheduled tasks
- ✅ **js/css** - Asset builders (development only)

### Service Communication

```
┌─────────────┐
│    web      │◄──── HTTP Requests (port 8000)
│  (Django)   │
└──────┬──────┘
       │
       ├─────► PostgreSQL (data storage)
       ├─────► Redis (cache/sessions)
       └─────► Redis (Celery broker)
                  │
                  ├─────► Celery Worker (async tasks)
                  └─────► Celery Beat (scheduled tasks)
```

## Next Steps

### 1. Rename the Project

The project is currently named "adlab". Rename it to match your system:

```bash
# Rename script (included in repo)
bin/rename-project laboratory Laboratory

# This will:
# - Find/replace "adlab" → "laboratory"
# - Update Docker resources
# - Optionally init new git repo
```

### 2. Install Laboratory System Dependencies

Update `pyproject.toml` with our required packages:

```toml
dependencies = [
    "Django>=5.2,<5.3",
    "psycopg[binary]>=3.1",
    "redis>=5.0",
    "celery[redis]>=5.4",
    "django-celery-beat>=2.6",
    "weasyprint>=60",
    "Pillow>=10",
    "python-qrcode[pil]>=7.4",
    "django-crispy-forms>=2.1",
    "crispy-tailwind>=0.5",
    "django-htmx>=1.17",
    "gunicorn>=21",
]
```

Then run:
```bash
./run deps:install
```

### 3. Create Django Apps

Create the application structure:

```bash
# Inside the web container
docker compose exec web bash

# Create apps for each step
python manage.py startapp accounts
python manage.py startapp veterinarians
python manage.py startapp protocols
python manage.py startapp reception
python manage.py startapp processing
python manage.py startapp reports
python manage.py startapp workorders
python manage.py startapp notifications
python manage.py startapp dashboard
python manage.py startapp analytics
```

### 4. Configure Django Settings

Update `src/config/settings.py`:

```python
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'crispy_forms',
    'crispy_tailwind',
    'django_htmx',
    'django_celery_beat',
    
    # Local apps
    'accounts',
    'veterinarians',
    'protocols',
    'reception',
    'processing',
    'reports',
    'workorders',
    'notifications',
    'dashboard',
    'analytics',
]
```

## Useful Commands

### Docker Compose

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View running services
docker compose ps

# Rebuild images
docker compose build

# Remove all containers and volumes
docker compose down -v
```

### Django Management

```bash
# Make migrations
./run manage makemigrations

# Apply migrations
./run manage migrate

# Create superuser
./run manage createsuperuser

# Run development server (alternative)
./run manage runserver

# Collect static files
./run manage collectstatic --noinput
```

### Celery

```bash
# View worker logs
docker compose logs -f worker

# View beat logs
docker compose logs -f beat

# Restart worker
docker compose restart worker

# Restart beat
docker compose restart beat
```

### Database

```bash
# Backup database
docker compose exec postgres pg_dump -U lab_user > backup.sql

# Restore database
docker compose exec -T postgres psql -U lab_user < backup.sql

# Access database shell
docker compose exec postgres psql -U lab_user
```

## Environment Variables

Key environment variables in `.env`:

```bash
# Project
COMPOSE_PROJECT_NAME=laboratory

# Services to run
COMPOSE_PROFILES=postgres,redis,assets,web,worker,beat

# Django
DEBUG=true
SECRET_KEY=insecure_key_for_dev  # Change in production!

# Database
POSTGRES_USER=lab_user
POSTGRES_PASSWORD=lab_password_dev

# Development
WEB_RELOAD=true  # Hot reload
DOCKER_WEB_PORT_FORWARD=8000  # Accessible on host
```

## Production Considerations

When deploying to production:

1. **Update .env for production:**
   ```bash
   export DEBUG=false
   export SECRET_KEY=<generate-secure-key>
   export POSTGRES_PASSWORD=<strong-password>
   export ALLOWED_HOSTS="laboratory.veterinaria.unl.edu.ar"
   export COMPOSE_PROFILES=postgres,redis,web,worker,beat  # No assets
   ```

2. **Use HTTPS:**
   - Add nginx reverse proxy
   - Configure SSL certificates

3. **Security:**
   - Never commit .env file
   - Use strong passwords
   - Enable firewall rules
   - Regular backups

4. **Monitoring:**
   - Set up logging
   - Configure Sentry
   - Monitor Celery queues

## Troubleshooting

### Port Already in Use

```bash
# If port 8000 is in use
export DOCKER_WEB_PORT_FORWARD=8001
```

### Database Connection Error

```bash
# Wait for postgres to be ready
docker compose exec web python manage.py wait_for_db
```

### Permission Errors

```bash
# Fix ownership
sudo chown -R $USER:$USER .
```

### Asset Build Errors

```bash
# Rebuild assets
docker compose up js css
```

## Documentation References

- **Original Template:** https://github.com/nickjj/docker-django-example
- **Django Docs:** https://docs.djangoproject.com/en/5.2/
- **Celery Docs:** https://docs.celeryq.dev/
- **Docker Compose:** https://docs.docker.com/compose/
- **Laboratory Steps:** See `/steps/README.md`
- **Tech Stack:** See `/TECH_STACK.md`

## Support

For issues specific to:
- **Template setup:** Check [docker-django-example issues](https://github.com/nickjj/docker-django-example/issues)
- **Laboratory features:** See project documentation in `/steps/`

---

**Ready to develop!** 🚀

Next: Follow the implementation steps in `/steps/step-01-authentication.md`

