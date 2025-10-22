# Setup Documentation

Get your laboratory system up and running.

## 📑 Contents

### [Quick Start Guide](./quickstart.md)
5-minute guide to get the system running locally with Docker Compose.

**When to use**: First time setup, development environment

### [Laboratory Workflow](./laboratory-workflow.md)
Understanding how the laboratory system works: from protocol submission to report delivery.

**When to use**: Understanding business processes, training new users

### [Test Credentials](./test-credentials.md)
Development and testing user accounts for all roles (veterinarian, histopathologist, lab staff, admin).

**When to use**: Testing, development, demonstration

## 🎯 Recommended Path

1. **First Timer?** Start with [Quick Start Guide](./quickstart.md)
2. **Need test users?** Check [Test Credentials](./test-credentials.md)
3. **Want to understand the workflow?** Read [Laboratory Workflow](./laboratory-workflow.md)

## ⚡ Quick Commands

```bash
# Start the system
docker compose up --build

# Run migrations
./run manage migrate

# Create superuser
./run manage createsuperuser

# Run tests
./run manage test
```

## 🔗 Related Documentation

- [Deployment](../deployment/) - Deploy to production
- [Configuration](../configuration/) - Configure settings
- [Operations](../operations/) - Daily operations

---

[← Back to Documentation Home](../README.md)
