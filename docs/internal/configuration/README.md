# Configuration Documentation

Configure system settings, integrations, and security.

## 📑 Contents

### [Email Setup](./email-setup.md)
Configure SMTP for sending email notifications (reports, verification emails, etc.).

**When to use**: Production deployment, testing email functionality

### [Environment Variables](./environment-variables.md)
Complete reference for all `.env` configuration options.

**When to use**: Initial setup, troubleshooting configuration issues

### [Security Audit](./security-audit.md)
Security checklist and hardening guide for production deployments.

**When to use**: Before production launch, security reviews

## 🎯 Configuration Workflow

### Initial Setup
```
1. Copy .env.example → .env
2. Edit environment variables
3. Configure email (if needed)
4. Review security settings
```

### Production Checklist
```
✅ DEBUG=false
✅ Strong SECRET_KEY generated
✅ ALLOWED_HOSTS configured
✅ Database password changed
✅ Email configured and tested
✅ Security audit completed
```

## ⚡ Quick Configuration

### Essential Variables
```bash
# .env file
SECRET_KEY=<generate-with-./run-secret>
DEBUG=false
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
POSTGRES_PASSWORD=<strong-password>
```

### Email Configuration
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## 🔒 Security Priority

1. **Always** change `SECRET_KEY` in production
2. **Never** commit `.env` files to git
3. **Use** strong database passwords
4. **Enable** HTTPS in production
5. **Review** security audit before launch

## 🔗 Related Documentation

- [Deployment](../deployment/) - Deployment procedures
- [Operations](../operations/) - Daily operations
- [Setup](../setup/) - Development setup

---

[← Back to Documentation Home](../README.md)
