# Deployment Documentation

Deploy the laboratory system to various environments.

## 📑 Contents

### [Local Development](./local-development.md)
Set up the complete development environment with Docker Compose.

**When to use**: Development, testing new features

### [Production Deployment](./production-deployment.md)
**⭐ Main deployment guide** - Complete instructions for deploying to a production server.

**When to use**: Initial production deployment, production updates

### [Nginx Setup](./nginx-setup.md)
Configure Nginx as a reverse proxy for the application.

**When to use**: Production deployment, performance optimization

### [SSL Certificates](./ssl-certificates.md)
Set up HTTPS with Let's Encrypt SSL certificates.

**When to use**: Production deployment, security compliance

### [VM Testing](./vm-testing.md)
Test deployment in a local VM before deploying to production servers.

**When to use**: Testing deployment procedures, training

### [Server Connection](./server-connection.md)
SSH access and server connection instructions.

**When to use**: Server setup, remote management

## 🎯 Deployment Paths

### Path 1: Local Development
```
1. Local Development → Start developing
```

### Path 2: Production Deployment
```
1. Server Connection → Connect to server
2. Production Deployment → Deploy application
3. Nginx Setup → Configure reverse proxy
4. SSL Certificates → Enable HTTPS
5. ../operations/production-checklist.md → Verify deployment
```

### Path 3: Testing Before Production
```
1. VM Testing → Test in local VM
2. [When confident] → Follow Path 2 for production
```

## ⚡ Quick Start Commands

### Development
```bash
docker compose up --build
./run manage migrate
```

### Production
```bash
docker compose -f compose.production.yaml up -d --build
./run manage migrate
./run manage collectstatic --no-input
```

## 🚨 Before Deploying to Production

✅ Review [Production Checklist](../operations/production-checklist.md)
✅ Configure [Environment Variables](../configuration/environment-variables.md)
✅ Set up [Email](../configuration/email-setup.md)
✅ Review [Security Audit](../configuration/security-audit.md)
✅ Plan [Backup Strategy](../operations/backup-restore.md)

## 🔗 Related Documentation

- [Configuration](../configuration/) - System configuration
- [Operations](../operations/) - Post-deployment operations
- [Setup](../setup/) - Development setup

---

[← Back to Documentation Home](../README.md)
