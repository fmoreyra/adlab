# Storage & Backup Implementation Guide

## Quick Reference

This guide provides a quick reference for implementing MinIO object storage and comprehensive backup/restore procedures for the AdLab Veterinary Laboratory system.

**Full documentation**: See `main-project-docs/steps/step-14-storage-backup.md`

## Quick Start

### 1. Start MinIO

```bash
# Add MinIO profile
docker compose --profile minio up -d

# Initialize buckets
docker compose exec web ./bin/minio-init

# Access MinIO Console
# URL: http://localhost:9001
# User: adlab_admin
# Password: (from .env)
```

### 2. Enable S3 Storage

Update `.env`:
```bash
USE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=adlab_admin
AWS_SECRET_ACCESS_KEY=your_secure_password
AWS_STORAGE_BUCKET_NAME=adlab-media
AWS_S3_ENDPOINT_URL=http://minio:9000
```

Restart application:
```bash
docker compose restart web worker
```

### 3. Run Manual Backup

```bash
# Database backup
./bin/backup-database

# File backup
./bin/backup-files

# Complete system backup
./bin/backup-complete
```

### 4. Test Restore

```bash
# List available backups
ls -lh /backups/database/daily/

# Restore database
./bin/restore-database /backups/database/daily/.../backup.sql.gz

# Restore files
./bin/restore-files /backups/files/backup.tar.gz
```

### 5. Enable Automated Backups

```bash
# Start backup service
docker compose --profile backup up -d

# Verify cron schedule
docker compose exec backup crontab -l
```

## Common Operations

### View Backup Status

```bash
# Run verification
./bin/verify-backups

# Check MinIO storage
docker compose exec web mc du adlab/adlab-media
docker compose exec web mc du adlab/adlab-backups
```

### Emergency Restore

```bash
# Complete system restore
./bin/restore-complete /backups/complete/latest.tar.gz --force
```

### Clean Up Old Backups

```bash
# Automatic cleanup happens during backup
# Manual cleanup:
find /backups/database -name "*.sql.gz" -mtime +30 -delete
```

## Backup Schedule

- **Hourly**: File sync to MinIO
- **Daily 2 AM**: Database backup
- **Daily 3 AM**: File archive backup
- **Sunday 4 AM**: Complete system backup
- **Monthly 1st**: Backup verification

## Storage Structure

```
MinIO Buckets:
├── adlab-media/          # Application files
│   ├── signatures/       # Histopathologist signatures
│   ├── reports/          # Generated PDF reports
│   ├── microscopy/       # Microscopy images
│   └── labels/           # QR code labels
│
└── adlab-backups/        # Backup storage
    ├── database/         # Database dumps
    ├── files/            # File archives
    └── complete/         # Complete system backups
```

## Monitoring

### Check Backup Health

```bash
# View recent backups
ls -lh /backups/database/daily/ | tail -5

# Check MinIO health
docker compose exec web mc admin info adlab

# View backup logs
tail -f /var/log/backup.log
```

### Alerts to Set Up

1. Backup failure notifications
2. Storage space warnings (>80%)
3. MinIO service down
4. Restore test failures

## Troubleshooting

### MinIO Not Accessible

```bash
# Check service
docker compose ps minio

# Restart MinIO
docker compose restart minio

# Check logs
docker compose logs minio
```

### Backup Failed

```bash
# Check logs
cat /var/log/backup.log

# Check disk space
df -h /backups

# Manual backup
./bin/backup-database
```

### Restore Failed

```bash
# Check backup integrity
gunzip -t backup.sql.gz

# Verify checksum
sha256sum -c backup.sql.gz.sha256

# Try different backup
ls -lh /backups/database/daily/
```

## Security Best Practices

1. **Rotate MinIO credentials** every 90 days
2. **Encrypt backups** before off-site storage
3. **Test restores** monthly
4. **Keep 3 copies** of critical data (3-2-1 rule)
5. **Restrict MinIO access** to internal network only
6. **Monitor access logs** regularly

## Next Steps

1. ✅ Implement Step 14 (see full documentation)
2. Configure off-site backup replication
3. Set up monitoring and alerts
4. Document disaster recovery procedures
5. Train team on restore procedures
6. Perform quarterly disaster recovery drills

## Support

For issues or questions:
1. Check full documentation: `main-project-docs/steps/step-14-storage-backup.md`
2. Review logs: `/var/log/backup.log`
3. Check MinIO console: http://localhost:9001
4. Contact system administrator

---

**⚠️ Important**: Always test restore procedures before relying on backups in production!

