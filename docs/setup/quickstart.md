# Quick Start Guide

Get the Laboratory Management System running on your local machine in 5 minutes.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed
- [Docker Compose](https://docs.docker.com/compose/install/) v2.20.2+ installed
- Git installed
- Terminal/Command line access

**System Requirements:**
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space
- macOS, Windows, or Linux

## Quick Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url> laboratory-system
cd laboratory-system
```

### 2. Copy Environment File

```bash
cp .env.example .env
```

The default `.env` file is pre-configured for development. No changes needed to get started!

### 3. Build and Start Services

```bash
# Build Docker images and start all services
docker compose up --build
```

**First-time build takes 5-10 minutes** depending on your internet connection. Docker will download images and install dependencies.

You'll see logs from all services. Wait for the message: `Listening at: http://0.0.0.0:8000`

### 4. Setup Database (in a new terminal)

Open a second terminal in the same directory:

```bash
# Run database migrations
./run manage migrate

# Create a superuser account
./run manage createsuperuser
```

Follow the prompts to create your admin account.

### 5. Access the Application

Open your browser and navigate to:

**[http://localhost:8000](http://localhost:8000)**

You should see the laboratory system home page!

## Next Steps

### Explore the System

- **Admin Interface**: [http://localhost:8000/admin](http://localhost:8000/admin)
  - Login with the superuser you created
  - Create test users and explore the data models

- **User Registration**: [http://localhost:8000/accounts/register](http://localhost:8000/accounts/register)
  - Register as a veterinarian (requires email verification in dev)
  - In development, check console logs for verification emails

### Load Test Data

```bash
# Create test users for all roles
./run manage shell < simple_test_data.py
```

This creates:
- Veterinarian: `vet@example.com` / `testpass123`
- Histopathologist: `histo@example.com` / `testpass123`
- Lab Staff: `staff@example.com` / `testpass123`

See [Test Credentials](./test-credentials.md) for complete list.

### Run Tests

```bash
# Run the full test suite
./run manage test

# Run specific app tests
./run manage test accounts
./run manage test protocols

# Run specific test file
./run manage test protocols.tests.ProtocolTestCase
```

### Check Code Quality

```bash
# Lint Python code
./run lint

# Format Python code
./run format

# Run all quality checks
./run quality
```

## Common Development Tasks

### View Logs

```bash
# View all service logs
docker compose logs -f

# View specific service
docker compose logs -f web
docker compose logs -f postgres
docker compose logs -f worker
```

### Stop the Application

```bash
# Stop all services (Ctrl+C in the terminal running docker compose up)
# OR
docker compose down
```

### Start Again

```bash
# Start services (much faster after first build)
docker compose up
```

### Reset Database

```bash
# Stop services
docker compose down

# Remove database volume
docker volume rm laboratory-system_postgres

# Start and migrate
docker compose up -d
./run manage migrate
./run manage createsuperuser
```

### Access Django Shell

```bash
# Python shell with Django
./run manage shell

# Access PostgreSQL
./run psql

# Access Redis CLI
./run redis-cli
```

### Update Dependencies

```bash
# Check outdated packages
./run uv:outdated
./run yarn:outdated

# After updating pyproject.toml or package.json
./run deps:install

# Rebuild containers
docker compose up --build
```

## Development Workflow

### Typical Development Session

```bash
# 1. Start services
docker compose up

# 2. (In another terminal) Make code changes
vim src/accounts/views.py

# 3. Changes auto-reload (no restart needed for most Python code)
# Watch the logs to see the reload

# 4. Run tests for what you changed
./run manage test accounts.test_views

# 5. Check code quality before committing
./run quality
```

### Database Migrations

```bash
# After changing models
./run manage makemigrations

# Apply migrations
./run manage migrate

# View migration SQL (optional)
./run manage sqlmigrate accounts 0001

# Show migration status
./run manage showmigrations
```

## Troubleshooting

### Port 8000 Already in Use

```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process or change port in .env
DOCKER_WEB_PORT_FORWARD=8001
```

### Permission Denied Errors

```bash
# Check UID/GID in .env (Linux users)
id  # Check your uid:gid

# Update .env if needed
UID=1000
GID=1000

# Rebuild
docker compose down
docker compose up --build
```

### Database Connection Errors

```bash
# Check if postgres is running
docker compose ps postgres

# View postgres logs
docker compose logs postgres

# Restart postgres
docker compose restart postgres
```

### Changes Not Reflecting

```bash
# For Python code changes - should auto-reload
# Check logs for "Reloading..."

# For static files (CSS/JS)
# Rebuild assets
docker compose restart assets

# For Docker/environment changes
# Full rebuild
docker compose down
docker compose up --build
```

### Tests Failing

```bash
# Clean up test database
./run test:cleanup

# Run tests again
./run manage test

# Run with verbose output
./run manage test --verbosity=2
```

## Development Tools

### Django Debug Toolbar

Enabled automatically in development:
- Visit any page
- Click the debug toolbar on the right side
- View SQL queries, templates, cache hits, etc.

### Interactive Debugger

Use `breakpoint()` in your Python code:

```python
def my_view(request):
    breakpoint()  # Execution will pause here
    # ... rest of code
```

Then interact in the terminal where `docker compose up` is running.

### Watch Mode for Frontend Assets

Assets (CSS/JS) automatically rebuild when you edit them. Check the `assets` service logs:

```bash
docker compose logs -f assets
```

## What's Running?

After `docker compose up`, you have:

- **web**: Django application server (port 8000)
- **postgres**: PostgreSQL database (port 5432)
- **redis**: Redis cache (port 6379)
- **worker**: Celery worker (background tasks)
- **beat**: Celery beat scheduler
- **assets**: esbuild + TailwindCSS watcher

## Next Steps

Now that you're up and running:

1. **Understand the workflow**: Read [Laboratory Workflow](./laboratory-workflow.md)
2. **Explore test data**: Check [Test Credentials](./test-credentials.md)
3. **Learn the architecture**: Read [CLAUDE.md](../../CLAUDE.md)
4. **Configure for your needs**: See [Configuration](../configuration/)
5. **Deploy to production**: See [Deployment Guide](../deployment/production-deployment.md)

## Getting Help

- **Troubleshooting**: See [Troubleshooting Guide](../operations/troubleshooting.md)
- **Full Setup Guide**: See [Laboratory Setup](./laboratory-workflow.md)
- **Documentation**: Browse [docs/](../)

---

[← Back to Setup Documentation](./README.md) | [Documentation Home](../README.md)
