# Storage & Backup Implementation Guide

## Quick Reference

This guide is **for future reference** when you implement the backup system. The current Step 14 scope is **Garage + Django only** (get Garage up and Django talking to it). Backups will be implemented **later**.

Quick reference for **Garage** object storage (now) and backup/restore procedures (later) for the AdLab Veterinary Laboratory system.

**Full documentation**: See `main-project-docs/steps/step-14-storage-backup.md`

---

## Garage Quick Start (Current Scope)

Use this section to get Garage running and Django using it. Backup steps below are for later.

### 1. Start Garage

[Garage](https://garagehq.deuxfleurs.fr/documentation/quick-start/) is S3-compatible object storage for self-hosting. Use path-style addressing and region `garage`.

```bash
# Create etc/garage.toml (see step-14), then:
docker compose --profile garage up -d

# One-time: layout assign, bucket create, key new, bucket allow (see step-14)
```

### 2. Enable S3 Storage

Update `.env`:

```bash
USE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=GKxxxx
AWS_SECRET_ACCESS_KEY=<secret_from_garage_key_new>
AWS_STORAGE_BUCKET_NAME=adlab-media
AWS_S3_ENDPOINT_URL=http://garage:3900
AWS_S3_REGION_NAME=garage
AWS_S3_ADDRESSING_STYLE=path
```

Restart application:
```bash
docker compose restart web worker
```

### 3. Configure mc for Backups (LATER)

When you implement backups:

```bash
export MC_REGION=garage
mc alias set adlab http://garage:3900 <KEY_ID> <SECRET> --api S3v4
```

### 4. Run Manual Backup (LATER)

When the backup system is implemented:

```bash
# Database backup
./bin/backup-database

# File backup
./bin/backup-files

# Complete system backup
./bin/backup-complete
```

### 5. Test Restore (LATER)

```bash
# List available backups
ls -lh /backups/database/daily/

# Restore database
./bin/restore-database /backups/database/daily/.../backup.sql.gz

# Restore files
./bin/restore-files /backups/files/backup.tar.gz
```

### 6. Enable Automated Backups (LATER)

```bash
# Start backup service
docker compose --profile backup up -d

# Verify cron schedule
docker compose exec backup crontab -l
```

## Backup & Restore (Future Reference)

The sections below apply when you implement the backup system later.

### View Backup Status

```bash
# Run verification
./bin/verify-backups

# Check Garage
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

- **Hourly**: File sync to Garage
- **Daily 2 AM**: Database backup
- **Daily 3 AM**: File archive backup
- **Sunday 4 AM**: Complete system backup
- **Monthly 1st**: Backup verification

## Storage Structure

```
Garage buckets:
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

# Check Garage (no admin API; use mc ls)
docker compose exec web mc ls adlab/adlab-media

# View backup logs
tail -f /var/log/backup.log
```

### Alerts to Set Up

1. Backup failure notifications
2. Storage space warnings (>80%)
3. Garage service down
4. Restore test failures

## Troubleshooting

### Garage Not Accessible

```bash
# Check service
docker compose ps garage

# Restart
docker compose restart garage

# Check logs
docker compose logs garage
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

1. **Rotate Garage key** every 90 days
2. **Encrypt backups** before off-site storage
3. **Test restores** monthly
4. **Keep 3 copies** of critical data (3-2-1 rule)
5. **Restrict object storage access** to internal network only
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
3. Garage: no web UI; use `garage status`, `garage bucket list`.
4. Contact system administrator

---

**⚠️ Important**: Always test restore procedures before relying on backups in production!

