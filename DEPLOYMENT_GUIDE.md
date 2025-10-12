# 🚀 Production Deployment Guide

**Laboratory Management System**  
**Version**: 1.0  
**Last Updated**: December 2024

---

## 📋 Overview

This guide provides complete instructions for deploying the Laboratory Management System to your production server (192.168.0.130). The deployment process is designed to be safe, automated, and includes rollback capabilities.

### Key Features

- **Zero-downtime deployment** with migrations-first approach
- **Automated database backups** before each deployment
- **Health checks** and service verification
- **Quick rollback** capability if issues arise
- **Pre-deployment validation** to catch issues early

---

## 🖥️ Server Requirements

### Minimum System Requirements

- **OS**: Ubuntu 20.04+ or CentOS 8+ (Linux recommended)
- **CPU**: 2 cores minimum, 4 cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB minimum free space
- **Network**: Stable internet connection for git pulls

### Required Software

- **Docker**: 20.10+ with Docker Compose v2
- **Git**: 2.25+
- **curl**: For health checks
- **gzip**: For backup compression

---

## 🔧 Initial Server Setup

### Option 1: Automated Setup (Recommended)

Use the automated setup script for a complete server configuration:

```bash
# Download and run the setup script
curl -fsSL https://raw.githubusercontent.com/your-username/laboratory-system/main/bin/setup-server -o setup-server.sh
chmod +x setup-server.sh

# Run automated setup
./setup-server.sh --repo https://github.com/your-username/laboratory-system.git --domain your-domain.com

# Or with SSH
./setup-server.sh --repo git@github.com:your-username/laboratory-system.git --domain your-domain.com
```

**Setup Script Features:**
- ✅ Updates system packages
- ✅ Installs Docker and Docker Compose
- ✅ Configures firewall (UFW) and fail2ban
- ✅ Creates application user and directory
- ✅ Clones repository
- ✅ Sets up environment configuration
- ✅ Configures systemd service
- ✅ Sets up log rotation
- ✅ Configures monitoring and backup scripts
- ✅ Runs initial deployment

### Option 2: Manual Setup

If you prefer manual setup, follow these steps:

#### 1. Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker compose version
```

#### 2. Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/laboratory-system
sudo chown $USER:$USER /opt/laboratory-system
cd /opt/laboratory-system

# Clone repository (replace with your actual repository URL)
git clone https://github.com/your-username/laboratory-system.git .

# Or if using SSH
git clone git@github.com:your-username/laboratory-system.git .
```

#### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment file for production
nano .env
```

**Required Environment Variables:**

```bash
# Django Settings
SECRET_KEY=your-super-secret-key-here-change-this
DEBUG=False
ALLOWED_HOSTS=192.168.0.130,your-domain.com

# Database
POSTGRES_USER=lab_user
POSTGRES_PASSWORD=secure-database-password
POSTGRES_DB=laboratory_db

# Email (CRITICAL - Configure SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.unl.edu.ar
EMAIL_PORT=587
EMAIL_HOST_USER=laboratorio@fcv.unl.edu.ar
EMAIL_HOST_PASSWORD=your-email-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=laboratorio@fcv.unl.edu.ar

# Security (Production)
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
```

#### 4. Initial Database Setup

```bash
# Build Docker images
docker compose build

# Start database and Redis
docker compose up -d postgres redis

# Wait for services to be ready
sleep 10

# Run initial migrations
./run manage migrate

# Create superuser
./run manage createsuperuser

# Collect static files
./run manage collectstatic --no-input
```

#### 5. Start All Services

```bash
# Start all services
docker compose up -d

# Verify services are running
docker compose ps

# Check logs
docker compose logs -f
```

---

## 🚀 Deployment Process

### Pre-deployment Checklist

Before each deployment, run the pre-deployment check:

```bash
# Run comprehensive pre-deployment checks
./bin/pre-deploy-check
```

This script will verify:
- ✅ Project directory structure
- ✅ Git repository status
- ✅ Environment configuration
- ✅ System resources (disk space, memory)
- ✅ Docker installation and status
- ✅ Database connectivity
- ✅ Redis connectivity
- ✅ Pending migrations
- ✅ Application health
- ✅ Security settings

### Deploy to Production

```bash
# Deploy latest changes
./bin/deploy
```

The deployment script will:
1. 🔍 **Validate** project directory and environment
2. 💾 **Backup** current database
3. 📥 **Pull** latest changes from git
4. 🏗️ **Build** new Docker images
5. 🔄 **Run** database migrations (if any)
6. 🚀 **Restart** services with zero downtime
7. ✅ **Verify** deployment health
8. 🧹 **Cleanup** old resources

### Monitor Deployment

```bash
# Watch application logs
docker compose logs -f web

# Check service status
docker compose ps

# Test application
curl http://localhost:8000/up
```

---

## 🔄 Rollback Process

If deployment issues occur, use the rollback script:

### Quick Rollback

```bash
# Interactive rollback (recommended)
./bin/rollback
```

### Advanced Rollback Options

```bash
# List available backups
./bin/rollback --list

# Restore specific backup
./bin/rollback --backup db_backup_20241201_143022.sql.gz

# Rollback to specific git commit
./bin/rollback --commit abc1234

# Force rollback (skip confirmations)
./bin/rollback --force
```

---

## 📊 Monitoring and Maintenance

### Automated Monitoring

The setup script configures automated monitoring:

```bash
# Check monitoring logs
tail -f /opt/laboratory-system/logs/monitor.log

# Run manual health check
/opt/laboratory-system/bin/monitor
```

**Monitoring includes:**
- Docker service status
- Container health
- Disk space usage
- Memory usage
- Application responsiveness

### Automated Backups

The setup script configures automated daily backups:

```bash
# Manual backup
/opt/laboratory-system/bin/backup

# Check backup directory
ls -la /tmp/lab-backups/

# Restore from backup (use rollback script)
./bin/rollback --backup /tmp/lab-backups/db_backup_YYYYMMDD_HHMMSS.sql.gz
```

### Health Checks

```bash
# Application health
curl http://localhost:8000/up

# Database connectivity
./run manage check --database default

# Redis connectivity
docker compose exec redis redis-cli ping

# Service status
docker compose ps
```

### Log Management

```bash
# View all logs
docker compose logs

# View specific service logs
docker compose logs web
docker compose logs worker
docker compose logs postgres

# Follow logs in real-time
docker compose logs -f web

# Check system logs
journalctl -u laboratory-system -f
```

### Database Maintenance

```bash
# Check database size
docker compose exec postgres psql -U lab_user -d laboratory_db -c "SELECT pg_size_pretty(pg_database_size('laboratory_db'));"

# List database tables
./run manage dbshell

# Run database checks
./run manage check --database default
```

### Service Management

```bash
# Start/stop/restart service
sudo systemctl start laboratory-system
sudo systemctl stop laboratory-system
sudo systemctl restart laboratory-system

# Check service status
sudo systemctl status laboratory-system

# View service logs
journalctl -u laboratory-system -f
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Docker Service Not Running

```bash
# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Check Docker status
sudo systemctl status docker
```

#### 2. Database Connection Issues

```bash
# Check PostgreSQL container
docker compose ps postgres

# Restart PostgreSQL
docker compose restart postgres

# Check database logs
docker compose logs postgres
```

#### 3. Application Not Responding

```bash
# Check web container
docker compose ps web

# Restart web service
docker compose restart web

# Check application logs
docker compose logs web
```

#### 4. Migration Failures

```bash
# Check migration status
./run manage showmigrations

# Check for migration conflicts
./run manage migrate --check

# Manual migration (if needed)
./run manage migrate --fake-initial
```

#### 5. Email Configuration Issues

```bash
# Test email configuration
./run manage shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

### Emergency Procedures

#### Complete System Restart

```bash
# Stop all services
docker compose down

# Start services
docker compose up -d

# Verify services
docker compose ps
```

#### Database Recovery

```bash
# Stop services
docker compose stop web worker beat

# Restore from backup
gunzip -c /tmp/lab-backups/db_backup_YYYYMMDD_HHMMSS.sql.gz | docker compose exec -T postgres psql -U lab_user -d laboratory_db

# Start services
docker compose up -d
```

#### Reset to Clean State

```bash
# WARNING: This will delete all data
docker compose down -v
docker system prune -a

# Rebuild from scratch
docker compose build
docker compose up -d
./run manage migrate
./run manage createsuperuser
```

---

## 🔒 Security Considerations

### Production Security Checklist

- [ ] **DEBUG=False** in environment
- [ ] **SECRET_KEY** changed from default
- [ ] **ALLOWED_HOSTS** configured for your domain
- [ ] **HTTPS enabled** (SESSION_COOKIE_SECURE=True)
- [ ] **Email SMTP** configured (not console backend)
- [ ] **Database passwords** are strong and unique
- [ ] **Firewall** configured (only necessary ports open)
- [ ] **Regular backups** scheduled
- [ ] **SSL certificates** installed and valid

### Firewall Configuration

```bash
# Allow SSH (port 22)
sudo ufw allow 22

# Allow HTTP (port 80) - if using reverse proxy
sudo ufw allow 80

# Allow HTTPS (port 443) - if using reverse proxy
sudo ufw allow 443

# Allow application port (port 8000) - only from local network
sudo ufw allow from 192.168.0.0/16 to any port 8000

# Enable firewall
sudo ufw enable
```

---

## 📈 Performance Optimization

### Resource Limits

Configure Docker resource limits in `compose.yaml`:

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### Database Optimization

```bash
# Check database performance
docker compose exec postgres psql -U lab_user -d laboratory_db -c "SELECT * FROM pg_stat_activity;"

# Analyze database size
docker compose exec postgres psql -U lab_user -d laboratory_db -c "SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

---

## 📞 Support and Maintenance

### Regular Maintenance Tasks

**Daily:**
- Monitor application logs
- Check service health
- Verify backup creation

**Weekly:**
- Review system resources
- Check for security updates
- Test backup restoration

**Monthly:**
- Update dependencies
- Review and rotate logs
- Performance analysis

### Contact Information

- **System Administrator**: [Your Name]
- **Email**: [your-email@domain.com]
- **Emergency Contact**: [emergency-contact]

### Documentation

- **Project Repository**: [GitHub URL]
- **Issue Tracker**: [GitHub Issues]
- **Technical Documentation**: [Project Docs]

---

## 📝 Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 2024 | Initial deployment guide |

---

**⚠️ Important Notes:**

1. **Always test deployments in a staging environment first**
2. **Keep database backups for at least 30 days**
3. **Monitor application logs after each deployment**
4. **Have a rollback plan ready before deploying**
5. **Document any custom configurations or changes**

---

*This deployment guide is part of the Laboratory Management System documentation. For technical support or questions, please refer to the project repository or contact the system administrator.*
