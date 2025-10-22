# Laboratory System Documentation

Welcome to the Laboratory Management System documentation. This guide will help you set up, deploy, configure, and operate the system.

## 📚 Documentation Structure

### 🚀 [Setup](./setup/)
Get started with the laboratory system:
- [Quick Start Guide](./setup/quickstart.md) - Get up and running in 5 minutes
- [Laboratory Workflow](./setup/laboratory-workflow.md) - Understanding the system's workflows
- [Test Credentials](./setup/test-credentials.md) - Development and testing accounts

### 🌐 [Deployment](./deployment/)
Deploy the system to development or production:
- [Local Development](./deployment/local-development.md) - Docker Compose setup for development
- [Production Deployment](./deployment/production-deployment.md) - Complete production deployment guide
- [Nginx Setup](./deployment/nginx-setup.md) - Reverse proxy configuration
- [SSL Certificates](./deployment/ssl-certificates.md) - HTTPS setup with Let's Encrypt
- [VM Testing](./deployment/vm-testing.md) - Test deployment in a VM before production
- [Server Connection](./deployment/server-connection.md) - SSH and server access

### ⚙️ [Configuration](./configuration/)
Configure system settings and integrations:
- [Email Setup](./configuration/email-setup.md) - Configure email notifications
- [Environment Variables](./configuration/environment-variables.md) - All configuration options
- [Security Audit](./configuration/security-audit.md) - Security checklist and hardening

### 🛠️ [Operations](./operations/)
Day-to-day operations and maintenance:
- [Backup & Restore](./operations/backup-restore.md) - Database backup procedures
- [Troubleshooting](./operations/troubleshooting.md) - Common issues and solutions
- [Production Checklist](./operations/production-checklist.md) - Pre-launch verification

### 📦 [Archive](./archive/)
**Implementation logs and project roadmap** (not just "old docs"!):
- [Development Steps](./archive/development-steps/) - **Implementation logs** showing which features are complete
- [Planning Documentation](./archive/planning/) - Feature specifications showing the full roadmap (20 steps planned, 10 complete)

**Important**: Missing `STEP_XX_COMPLETE.md` files indicate unresolved features or future work. See [Archive README](./archive/README.md) for implementation status.

## 🔗 Quick Links

- [Main README](../README.md) - Project overview and tech stack
- [CLAUDE.md](../CLAUDE.md) - Guide for Claude Code AI assistant
- [CHANGELOG](../CHANGELOG.md) - Version history and changes

## 🎯 Common Tasks

### First Time Setup
1. [Install Prerequisites](./setup/quickstart.md#prerequisites)
2. [Clone and Configure](./setup/quickstart.md#setup)
3. [Run Migrations](./setup/quickstart.md#database-setup)
4. [Create Test Users](./setup/test-credentials.md)

### Deploying to Production
1. [Prepare Server](./deployment/production-deployment.md#server-requirements)
2. [Install Dependencies](./deployment/production-deployment.md#installation)
3. [Configure Environment](./configuration/environment-variables.md)
4. [Setup Nginx & SSL](./deployment/nginx-setup.md)
5. [Configure Email](./configuration/email-setup.md)
6. [Run Checklist](./operations/production-checklist.md)

### Regular Operations
- [Backing Up Data](./operations/backup-restore.md#backup-procedures)
- [Monitoring Logs](./operations/troubleshooting.md#log-monitoring)
- [Updating the System](./operations/production-checklist.md#update-procedures)

## 📖 For Developers

If you're contributing to the codebase:
- Read [CLAUDE.md](../CLAUDE.md) for architecture overview and development patterns
- Check [Development History](./archive/development-steps/) for feature implementation details
- Review [Planning Docs](./archive/planning/) for design decisions and future roadmap

## 🆘 Getting Help

- Check [Troubleshooting Guide](./operations/troubleshooting.md) for common issues
- Review [Test Credentials](./setup/test-credentials.md) for development access
- Refer to [Production Checklist](./operations/production-checklist.md) for deployment issues

## 📝 Contributing to Documentation

When adding new documentation:
- Place setup guides in `setup/`
- Place deployment guides in `deployment/`
- Place configuration guides in `configuration/`
- Place operational procedures in `operations/`
- Update this README with links to new documents

---

**Need to get started quickly?** → [Quick Start Guide](./setup/quickstart.md)

**Ready to deploy?** → [Production Deployment Guide](./deployment/production-deployment.md)
