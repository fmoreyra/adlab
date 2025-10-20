# Technology Stack Documentation
## Sistema de Laboratorio de Anatomía Patológica Veterinaria

**Last Updated:** October 2025  
**Status:** APPROVED ✅

---

## 🎯 Core Technology Decisions

### Backend: Django 5.2 LTS
- **Version:** 5.2 (LTS - Long Term Support)
- **Support:** Until April 2028 (security until April 2029)
- **Python:** 3.10, 3.11, or 3.12
- **Why:** Mature, batteries-included, excellent for data-driven applications

### Database: PostgreSQL 16
- **Version:** PostgreSQL 16.x (latest stable)
- **Why:** 
  - Robust ACID compliance
  - Excellent for complex queries (analytics, reports)
  - JSON support for flexible fields
  - Strong backup/recovery tools
  - Perfect match with Django ORM

### Caching & Task Queue: Redis 7
- **Version:** Redis 7.x
- **Uses:**
  - Session storage
  - Celery message broker
  - Cache backend
  - Real-time data cache

### Frontend: HTMX + Alpine.js
- **HTMX 1.9+:** Dynamic HTML over the wire
- **Alpine.js 3.x:** Minimal JavaScript framework
- **Tailwind CSS 3.x:** Utility-first CSS framework
- **Why:** Modern interactivity without SPA complexity

---

## 📦 Complete Dependencies

### requirements.txt (Production)

```txt
# Django Core
Django==5.2.*
psycopg[binary]==3.1.*  # PostgreSQL adapter
python-dotenv==1.0.*    # Environment variables

# Forms & UI Enhancement
django-crispy-forms==2.1.*
crispy-tailwind==0.5.*
django-widget-tweaks==1.5.*

# HTMX Integration
django-htmx==1.17.*

# PDF & File Generation
weasyprint==60.*
Pillow==10.*
python-qrcode[pil]==7.4.*

# Email & Async Tasks
celery[redis]==5.4.*
django-celery-beat==2.6.*  # Scheduled tasks
redis==5.0.*

# Security & Authentication
django-allauth==0.57.*  # Optional: Enhanced auth
argon2-cffi==23.*       # Password hashing

# Storage & Files
django-storages==1.14.*  # Future cloud storage support

# API (if needed later)
djangorestframework==3.14.*  # Optional

# Monitoring & Logging
sentry-sdk==1.40.*  # Error tracking
```

### requirements-dev.txt (Development)

```txt
-r requirements.txt

# Development Tools
django-debug-toolbar==4.2.*
django-extensions==3.2.*
ipython==8.20.*

# Testing
pytest==7.4.*
pytest-django==4.7.*
pytest-cov==4.1.*
factory-boy==3.3.*  # Test data generation
faker==20.*

# Code Quality
black==23.*
flake8==6.*
isort==5.*
mypy==1.7.*
django-stubs==4.*

# Documentation
sphinx==7.*
sphinx-rtd-theme==2.*
```

---

## 🏗️ Project Structure

```
laboratory-system/
│
├── manage.py
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── README.md
├── docker-compose.yml
├── Dockerfile
│
├── config/                          # Project configuration
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                 # Base settings
│   │   ├── development.py          # Dev environment
│   │   ├── production.py           # Production environment
│   │   └── test.py                 # Test environment
│   ├── urls.py                     # Root URL configuration
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                            # Django applications
│   │
│   ├── core/                        # Core/shared functionality
│   │   ├── models.py               # Base models
│   │   ├── mixins.py               # Reusable mixins
│   │   ├── utils.py                # Utilities
│   │   └── templates/
│   │       └── core/
│   │           ├── base.html
│   │           ├── base_form.html
│   │           └── components/
│   │
│   ├── accounts/                    # Step 01: Authentication
│   │   ├── models.py               # User, Profile models
│   │   ├── forms.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── signals.py
│   │   └── templates/
│   │       └── accounts/
│   │           ├── login.html
│   │           ├── register.html
│   │           └── profile.html
│   │
│   ├── veterinarians/               # Step 02: Veterinarian Profiles
│   │   ├── models.py               # Veterinario, Domicilio
│   │   ├── forms.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── templates/
│   │       └── veterinarians/
│   │
│   ├── protocols/                   # Step 03: Protocol Submission
│   │   ├── models.py               # Protocol, Muestra
│   │   ├── forms.py                # CytologyForm, HistopathologyForm
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── templates/
│   │       └── protocols/
│   │           ├── submit_cytology.html
│   │           ├── submit_histopathology.html
│   │           ├── list.html
│   │           └── detail.html
│   │
│   ├── reception/                   # Step 04: Sample Reception
│   │   ├── models.py
│   │   ├── forms.py
│   │   ├── views.py
│   │   ├── utils.py                # Protocol numbering logic
│   │   ├── labels.py               # Label generation
│   │   └── templates/
│   │
│   ├── processing/                  # Step 05: Sample Processing
│   │   ├── models.py               # Cassette, Portaobjetos
│   │   ├── forms.py
│   │   ├── views.py
│   │   └── templates/
│   │
│   ├── reports/                     # Step 06: Report Generation
│   │   ├── models.py               # InformeResultados
│   │   ├── forms.py
│   │   ├── views.py
│   │   ├── pdf_generator.py        # PDF generation logic
│   │   └── templates/
│   │       ├── reports/
│   │       └── pdf/
│   │           └── report_template.html
│   │
│   ├── workorders/                  # Step 07: Work Orders
│   │   ├── models.py               # OrdenTrabajo, Pricing
│   │   ├── views.py
│   │   └── templates/
│   │
│   ├── notifications/               # Step 08: Email Notifications
│   │   ├── models.py               # Notification, Preferences
│   │   ├── tasks.py                # Celery tasks
│   │   ├── utils.py
│   │   └── templates/
│   │       └── emails/
│   │
│   ├── dashboard/                   # Step 09: Dashboard
│   │   ├── views.py
│   │   ├── metrics.py              # Metric calculations
│   │   └── templates/
│   │       └── dashboard/
│   │           ├── dashboard.html
│   │           └── partials/
│   │
│   └── analytics/                   # Step 10: Reports & Analytics
│       ├── views.py
│       ├── queries.py              # Complex analytical queries
│       ├── exports.py              # CSV/Excel export
│       └── templates/
│
├── templates/                       # Global templates
│   ├── base.html
│   ├── navigation.html
│   ├── footer.html
│   └── errors/
│       ├── 404.html
│       ├── 500.html
│       └── 403.html
│
├── static/                          # Static files
│   ├── css/
│   │   ├── main.css
│   │   └── tailwind.config.js
│   ├── js/
│   │   ├── htmx.min.js
│   │   ├── alpine.min.js
│   │   ├── chart.min.js
│   │   └── app.js
│   ├── img/
│   │   └── logo.png
│   └── fonts/
│
├── storage/                         # File storage (not in git)
│   ├── reports/
│   │   └── 2024/10/
│   ├── labels/
│   ├── signatures/
│   └── temp/
│
├── scripts/                         # Management scripts
│   ├── deploy.sh
│   ├── backup.sh
│   └── migrate_from_clarion.py     # Step 11: Data migration
│
├── tests/                           # Tests
│   ├── conftest.py
│   ├── factories.py
│   └── test_*.py
│
└── docs/                            # Additional documentation
    ├── deployment.md
    ├── api.md
    └── architecture.md
```

---

## 🐳 Docker Configuration

### Dockerfile

```dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "config.wsgi:application"]
```

### docker-compose.yml

```yaml
version: '3.9'

services:
  db:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=laboratory_db
      - POSTGRES_USER=lab_user
      - POSTGRES_PASSWORD=secure_password
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lab_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/storage
    ports:
      - "8000:8000"
    environment:
      - DEBUG=1
      - DATABASE_URL=postgresql://lab_user:secure_password@db:5432/laboratory_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery:
    build: .
    command: celery -A config worker -l info
    volumes:
      - .:/app
      - media_volume:/app/storage
    environment:
      - DATABASE_URL=postgresql://lab_user:secure_password@db:5432/laboratory_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
      - web

  celery-beat:
    build: .
    command: celery -A config beat -l info
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=postgresql://lab_user:secure_password@db:5432/laboratory_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

---

## ⚙️ Django Settings Structure

### config/settings/base.py (Excerpt)

```python
"""
Base settings for laboratory system.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')

# Application definition
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
    'apps.core',
    'apps.accounts',
    'apps.veterinarians',
    'apps.protocols',
    'apps.reception',
    'apps.processing',
    'apps.reports',
    'apps.workorders',
    'apps.notifications',
    'apps.dashboard',
    'apps.analytics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_htmx.middleware.HtmxMiddleware',  # HTMX support
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'laboratory_db'),
        'USER': os.getenv('DB_USER', 'lab_user'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Cache (Redis)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}

# Session (Redis)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 7200  # 2 hours

# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Argentina/Buenos_Aires'

# Internationalization
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files (User uploads)
MEDIA_URL = '/storage/'
MEDIA_ROOT = BASE_DIR / 'storage'

# Crispy Forms (Tailwind)
CRISPY_ALLOWED_TEMPLATE_PACKS = 'tailwind'
CRISPY_TEMPLATE_PACK = 'tailwind'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Password hashers (Argon2 for security)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.unl.edu.ar')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'lab@veterinaria.unl.edu.ar')
```

---

## 📝 Environment Variables (.env.example)

```bash
# Django
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=laboratory_db
DB_USER=lab_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.unl.edu.ar
EMAIL_PORT=587
EMAIL_HOST_USER=lab@veterinaria.unl.edu.ar
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=lab@veterinaria.unl.edu.ar

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0

# Security (Production)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Optional: Sentry for error tracking
SENTRY_DSN=
```

---

## 🚀 Getting Started

### 1. Initial Setup

```bash
# Clone repository (or initialize new project)
git clone <repository-url>
cd laboratory-system

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Copy environment file
cp .env.example .env
# Edit .env with your values
```

### 2. Database Setup

```bash
# Start PostgreSQL and Redis with Docker
docker-compose up -d db redis

# Create database migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data (if any)
python manage.py loaddata initial_data.json
```

### 3. Run Development Server

```bash
# Collect static files
python manage.py collectstatic --noinput

# Run server
python manage.py runserver

# In another terminal, run Celery worker
celery -A config worker -l info

# In another terminal, run Celery beat (scheduled tasks)
celery -A config beat -l info
```

### 4. Access the Application

- **Main App:** http://localhost:8000/
- **Admin Panel:** http://localhost:8000/admin/
- **API Docs:** http://localhost:8000/api/docs/ (if using DRF)

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test file
pytest tests/test_protocols.py

# Run with verbose output
pytest -v
```

---

## 📊 HTMX + Alpine.js Examples

### Example 1: Real-time Dashboard Widget

```html
<!-- templates/dashboard/dashboard.html -->
<div class="wip-widget" 
     hx-get="{% url 'dashboard:wip_data' %}"
     hx-trigger="load, every 60s"
     hx-swap="innerHTML">
  <p>Loading...</p>
</div>
```

### Example 2: Form with Inline Validation

```html
<!-- templates/protocols/submit_form.html -->
<form hx-post="{% url 'protocols:submit' %}"
      hx-target="#result"
      hx-swap="outerHTML">
  {% csrf_token %}
  {{ form|crispy }}
  
  <button type="submit" class="btn-primary">
    Enviar Protocolo
  </button>
</form>

<div id="result"></div>
```

### Example 3: Alpine.js for Client-side Interactivity

```html
<!-- Dropdown with Alpine.js -->
<div x-data="{ open: false }">
  <button @click="open = !open">
    Opciones
  </button>
  
  <div x-show="open" @click.away="open = false">
    <a href="#">Editar</a>
    <a href="#">Eliminar</a>
  </div>
</div>
```

---

## 🔒 Security Considerations

### Production Checklist

- [ ] Change `SECRET_KEY` to strong random value
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Enable HTTPS (`SECURE_SSL_REDIRECT=True`)
- [ ] Secure cookies (`SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`)
- [ ] Configure firewall rules
- [ ] Set up regular backups
- [ ] Enable logging and monitoring
- [ ] Use environment variables for secrets
- [ ] Configure Content Security Policy
- [ ] Set up rate limiting

---

## 📈 Performance Optimization

### Database

```python
# Use select_related and prefetch_related
protocols = Protocol.objects.select_related('veterinario').all()

# Use database indexes
class Protocol(models.Model):
    numero_protocolo = models.CharField(max_length=50, unique=True, db_index=True)
    fecha_recepcion = models.DateTimeField(db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['veterinario', 'fecha_recepcion']),
        ]
```

### Caching

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # Cache for 5 minutes
def dashboard_view(request):
    # Expensive computation
    return render(request, 'dashboard.html', context)
```

### Static Files

```python
# Use WhiteNoise for static file serving in production
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # After SecurityMiddleware
    # ...
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

---

## 📚 Additional Resources

### Django 5.2 Documentation
- Official docs: https://docs.djangoproject.com/en/5.2/
- Release notes: https://docs.djangoproject.com/en/5.2/releases/5.2/

### HTMX
- Documentation: https://htmx.org/docs/
- Examples: https://htmx.org/examples/

### Alpine.js
- Documentation: https://alpinejs.dev/
- Start here: https://alpinejs.dev/start-here

### WeasyPrint
- Documentation: https://doc.courtbouillon.org/weasyprint/

---

## 🆘 Common Issues & Solutions

### Issue: WeasyPrint installation fails
**Solution:** Install system dependencies first:
```bash
# Ubuntu/Debian
sudo apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# macOS
brew install cairo pango gdk-pixbuf libffi
```

### Issue: PostgreSQL connection refused
**Solution:** Check if PostgreSQL is running:
```bash
docker-compose ps
# Or if installed locally:
sudo service postgresql status
```

### Issue: Redis connection error
**Solution:** Start Redis:
```bash
docker-compose up -d redis
# Or if installed locally:
redis-server
```

---

**Ready to start development!** 🚀

Next steps:
1. Review this tech stack with team
2. Set up development environment
3. Begin Step 01 (Authentication) implementation
4. Follow the step-by-step guide in `/steps/`

