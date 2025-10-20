# Local Development Setup

Complete guide for setting up a local development environment.

## Overview

This guide covers setting up the laboratory system for local development using Docker Compose. For a quick 5-minute setup, see the [Quick Start Guide](../setup/quickstart.md).

## Prerequisites

### Required Software

- **Docker Desktop** (macOS/Windows) or **Docker Engine** (Linux)
  - Version 20.10+ with Docker Compose v2.20.2+
  - [Installation Guide](https://docs.docker.com/get-docker/)

- **Git** 2.25+
  - [Installation Guide](https://git-scm.com/downloads)

### System Requirements

**Minimum:**
- 4GB RAM
- 10GB free disk space
- Dual-core CPU

**Recommended:**
- 8GB+ RAM
- 20GB+ free disk space
- Quad-core CPU

### Optional Tools

- **Make** (for Makefile workflows - the standard way to run project tasks)
- **HTTPie or Postman** (for API testing)
- **pgAdmin** or **DBeaver** (for database management)
- **Redis Desktop Manager** (for Redis inspection)

## Initial Setup

### 1. Clone Repository

```bash
# Clone the repository
git clone <your-repository-url> laboratory-system
cd laboratory-system

# Check you're on the right branch
git branch
```

### 2. Configure Environment

```bash
# Copy the development environment template
cp .env.example .env
```

The `.env.example` file is pre-configured for development with sensible defaults:

```bash
# Key development settings
DEBUG=true
SECRET_KEY=insecure_key_for_dev
COMPOSE_PROFILES=postgres,redis,assets,web,worker

# Ports (change if conflicts)
DOCKER_WEB_PORT_FORWARD=8000
DOCKER_POSTGRES_PORT_FORWARD=5432
DOCKER_REDIS_PORT_FORWARD=6379

# Database
POSTGRES_USER=adlab
POSTGRES_PASSWORD=password
POSTGRES_DB=adlab
```

**For most development, you don't need to change anything in `.env`.**

### 3. Build Docker Images

```bash
# Build all images
docker compose build

# Or build with no cache (if you have issues)
docker compose build --no-cache
```

**First build takes 5-10 minutes** to download base images and install all dependencies.

### 4. Start Services

```bash
# Start all services
docker compose up

# Or start in background
docker compose up -d

# View logs if running in background
docker compose logs -f
```

### 5. Initialize Database

In a new terminal:

```bash
# Run migrations
make manage ARGS="migrate"

# Create superuser
make manage ARGS="createsuperuser"
# Follow prompts to create admin account

# (Optional) Load test data
make manage ARGS="shell" < simple_test_data.py
```

### 6. Verify Setup

```bash
# Check all services are running
docker compose ps

# Should see:
# - web (healthy)
# - postgres (healthy)
# - redis (healthy)
# - worker (running)
# - beat (running)
# - assets (running)

# Test the application
curl http://localhost:8000/up
# Should return: {"status":"ok",...}

# Access in browser
open http://localhost:8000
```

## Development Workflow

### Running the Application

```bash
# Start services (with logs visible)
docker compose up

# Start in background
docker compose up -d

# Stop services
docker compose down

# Stop and remove volumes (fresh start)
docker compose down -v
```

### Making Code Changes

#### Python Code Changes

Django automatically reloads when you change Python files:

```python
# Edit a file
vim src/accounts/views.py

# Watch the web service logs
# You'll see: "Reloading..."
# Changes are immediately active
```

#### Template Changes

Templates are reloaded automatically:

```bash
# Edit a template
vim src/templates/pages/home.html

# Refresh browser - changes are live
```

#### Static Files (CSS/JS)

The `assets` service watches and rebuilds automatically:

```bash
# Edit CSS or JS
vim assets/css/app.css

# Watch assets service logs
docker compose logs -f assets

# Refresh browser - changes are live
```

#### Django Model Changes

After changing models, create and apply migrations:

```bash
# Create migration
make manage ARGS="makemigrations"

# Review the migration
cat src/accounts/migrations/0002_*.py

# Apply migration
make manage ARGS="migrate"

# (Optional) View SQL
make manage ARGS="sqlmigrate accounts 0002"
```

### Running Tests

```bash
# Run all tests
make test

# Run tests for specific app
make manage ARGS="test accounts"
make manage ARGS="test protocols"

# Run specific test class
make manage ARGS="test protocols.tests.ProtocolTestCase"

# Run specific test method
make manage ARGS="test protocols.tests.ProtocolTestCase.test_create_protocol"

# Run with verbose output
make manage ARGS="test --verbosity=2"

# Run with coverage
docker compose exec web pytest --cov
```

### Code Quality

```bash
# Lint Python code
make lint

# Auto-fix linting issues
make format

# Run all quality checks
make quality

# Individual checks
make lint-dockerfile
make lint-shell
make format-shell
```

### Database Operations

```bash
# Access PostgreSQL CLI
make psql

# Within psql:
\dt                    # List tables
\d protocols_protocol  # Describe table
SELECT COUNT(*) FROM accounts_user;

# Backup database
make db-dump
# Creates: backups/adlab_dump_YYYYMMDD_HHMMSS.sql

# Reset database (careful!)
docker compose down -v
docker compose up -d
make manage ARGS="migrate"
```

### Django Management Commands

```bash
# Django shell
make manage ARGS="shell"

# Create superuser
make manage ARGS="createsuperuser"

# Check for issues
make manage ARGS="check"

# Show migrations
make manage ARGS="showmigrations"

# Collect static files
make manage ARGS="collectstatic"

# Send test email
make manage ARGS="sendtestemail you@example.com"

# Custom commands (if you create them)
make manage ARGS="your_custom_command"
```

### Celery Tasks

```bash
# View worker logs
docker compose logs -f worker

# View beat scheduler logs
docker compose logs -f beat

# Access Redis CLI
make redis-cli

# Within redis-cli:
KEYS *          # List all keys
GET some_key    # Get value
FLUSHDB         # Clear database (careful!)
```

## Development Tools

### Django Debug Toolbar

Automatically enabled in development (`DEBUG=true`):

1. Visit any page in the application
2. Look for the debug toolbar on the right side
3. Click to expand and view:
   - SQL queries and performance
   - Template rendering info
   - Cache hits/misses
   - HTTP headers
   - Request/response data

### Interactive Debugging

Use Python's `breakpoint()` for interactive debugging:

```python
# In any Python file
def my_view(request):
    user = request.user
    breakpoint()  # Execution pauses here
    # ... rest of code
```

When code hits the breakpoint:
- Terminal shows interactive debugger (pdb)
- Type `c` to continue, `n` for next line, `p variable` to print
- Type `help` for all commands

### Hot Reloading

#### Django (Python)
- ✅ Auto-reloads on `.py` file changes
- ✅ Auto-reloads on template changes
- ❌ Requires restart for `.env` changes
- ❌ Requires rebuild for `pyproject.toml` changes

#### Assets (CSS/JS)
- ✅ Auto-rebuilds on CSS changes
- ✅ Auto-rebuilds on JS changes
- ✅ TailwindCSS classes detected automatically
- Just refresh browser to see changes

### Database Inspection

Use external tools to inspect the database:

**pgAdmin:**
```
Host: localhost
Port: 5432
User: adlab
Password: password
Database: adlab
```

**DBeaver:**
Same connection settings as pgAdmin.

**TablePlus (macOS):**
Same connection settings, nice UI.

## Common Development Tasks

### Creating a New Django App

```bash
# Create app structure
make manage ARGS="startapp myapp src/myapp"

# Add to INSTALLED_APPS in src/config/settings.py
INSTALLED_APPS = [
    'myapp.apps.MyappConfig',
    ...
]

# Create models, views, etc.
```

### Adding Python Dependencies

```bash
# Edit pyproject.toml
vim pyproject.toml

# Add your package
[project]
dependencies = [
    "django>=5.2",
    "your-package>=1.0",
]

# Install dependencies
make deps-install

# Rebuild containers
docker compose up --build
```

### Adding JavaScript Dependencies

```bash
# Add to package.json
cd assets
vim package.json

# Install
make yarn-install

# Rebuild
docker compose up --build
```

### Working with Migrations

```bash
# Create migration
make manage ARGS="makemigrations"

# Create empty migration (for data or custom operations)
make manage ARGS="makemigrations --empty myapp"

# Apply migrations
make manage ARGS="migrate"

# Rollback last migration
make manage ARGS="migrate myapp 0001"

# Show migration SQL
make manage ARGS="sqlmigrate myapp 0002"

# Squash migrations
make manage ARGS="squashmigrations myapp 0001 0005"
```

### Creating Fixtures

```bash
# Dump data to fixture
make manage ARGS="dumpdata accounts.User --indent=2" > src/accounts/fixtures/users.json

# Load fixture
make manage ARGS="loaddata users"

# Dump entire database
make manage ARGS="dumpdata --indent=2" > backup.json
```

## Troubleshooting

### Services Won't Start

```bash
# Check what's running
docker compose ps

# View logs for specific service
docker compose logs web
docker compose logs postgres

# Restart specific service
docker compose restart web

# Full restart
docker compose down
docker compose up
```

### Port Conflicts

If ports are already in use:

```bash
# Check what's using port 8000
lsof -i :8000

# Change port in .env
DOCKER_WEB_PORT_FORWARD=8001

# Restart
docker compose down
docker compose up
```

### Permission Issues (Linux)

```bash
# Check your uid:gid
id

# Update .env
UID=1000
GID=1000

# Rebuild
docker compose down
docker compose up --build
```

### Database Issues

```bash
# Reset database completely
docker compose down -v
docker compose up -d
make manage ARGS="migrate"

# Check database connectivity
make psql ARGS="-c \"SELECT version();\""

# View postgres logs
docker compose logs postgres
```

### Asset Build Issues

```bash
# Rebuild assets
docker compose restart assets

# View asset logs
docker compose logs -f assets

# Manually rebuild
docker compose exec assets npm run build
```

### Test Database Issues

```bash
# Clean up test database
make test-cleanup

# Run tests again
make test
```

## Performance Tips

### Speed Up Development

1. **Use BuildKit**:
   ```bash
   export DOCKER_BUILDKIT=1
   ```

2. **Mount fewer files** (if issues):
   - Comment out unnecessary volume mounts in `docker-compose.yml`

3. **Increase Docker resources**:
   - Docker Desktop → Settings → Resources
   - Increase CPUs and Memory

4. **Use `.dockerignore`**:
   - Ensure large files/dirs are excluded

5. **Persistent volumes**:
   - Don't use `docker compose down -v` unless necessary

### Reduce Memory Usage

```bash
# Stop unused services
docker compose stop beat  # If not testing scheduled tasks

# Clean up Docker
docker system prune -a

# Remove unused volumes
docker volume prune
```

## Environment Profiles

### Default Development Profile

```bash
# All services (default)
COMPOSE_PROFILES=postgres,redis,assets,web,worker
docker compose up
```

### Minimal Profile (Just App)

```bash
# Only web server (for quick testing)
COMPOSE_PROFILES=postgres,redis,web
docker compose up
```

### Testing Profile

```bash
# For running tests (no beat, no assets)
COMPOSE_PROFILES=postgres,redis,web,worker
docker compose up -d
make test
```

## Next Steps

Now that you have local development working:

1. **Explore Features**: Check [Laboratory Workflow](../setup/laboratory-workflow.md)
2. **Review Architecture**: Read [CLAUDE.md](../../CLAUDE.md)
3. **Configure System**: See [Configuration Guide](../configuration/)
4. **Deploy to Production**: See [Production Deployment](./production-deployment.md)

## Related Documentation

- [Quick Start](../setup/quickstart.md) - Fast setup guide
- [Test Credentials](../setup/test-credentials.md) - Test user accounts
- [CLAUDE.md](../../CLAUDE.md) - Architecture and development patterns
- [Troubleshooting](../operations/troubleshooting.md) - Common issues

---

[← Back to Deployment Documentation](./README.md) | [Documentation Home](../README.md)
