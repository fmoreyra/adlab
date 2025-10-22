# Operations Documentation

Day-to-day operations, maintenance, and troubleshooting.

## 📑 Contents

### [Backup & Restore](./backup-restore.md)
Database backup procedures and restore operations.

**When to use**: Daily backups, disaster recovery, data migration

### [Troubleshooting](./troubleshooting.md)
Common issues and their solutions.

**When to use**: Debugging problems, error resolution

### [Production Checklist](./production-checklist.md)
Pre-launch verification checklist for production deployments.

**When to use**: Before going live, after major updates

## 🎯 Common Operations

### Daily Tasks
- Monitor application logs
- Review system health
- Check backup completion

### Weekly Tasks
- Review and archive old backups
- Check disk space usage
- Review error logs

### Monthly Tasks
- System updates
- Security patches
- Performance review

## ⚡ Quick Operations

### Backup Database
```bash
./run db:dump
# Creates: backups/adlab_dump_YYYYMMDD_HHMMSS.sql
```

### View Logs
```bash
# Application logs
docker compose logs -f web

# All services
docker compose logs -f

# Specific service
docker compose logs -f postgres
```

### Restart Services
```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart web
```

### Check System Health
```bash
# Service status
docker compose ps

# Resource usage
docker stats

# Database connection
./run psql -c "SELECT version();"
```

## 🚨 Emergency Procedures

### Application Down
1. Check logs: `docker compose logs -f web`
2. Check service status: `docker compose ps`
3. Restart if needed: `docker compose restart web`
4. Review [Troubleshooting](./troubleshooting.md)

### Database Issues
1. Check PostgreSQL logs: `docker compose logs -f postgres`
2. Test connection: `./run psql -c "SELECT 1;"`
3. If needed, restore from backup: [Backup & Restore](./backup-restore.md)

### Disk Space Full
1. Check usage: `df -h`
2. Clean up: `docker system prune -a`
3. Archive old backups
4. Review log file sizes

## 📊 Monitoring

### Key Metrics to Watch
- Response time
- Error rates
- Database connections
- Disk space
- Memory usage
- CPU usage

### Log Files
- Application: `docker compose logs web`
- PostgreSQL: `docker compose logs postgres`
- Nginx: `/var/log/nginx/`
- Celery: `docker compose logs worker`

## 🔗 Related Documentation

- [Deployment](../deployment/) - Deployment procedures
- [Configuration](../configuration/) - System configuration
- [Setup](../setup/) - Development setup

---

[← Back to Documentation Home](../README.md)
