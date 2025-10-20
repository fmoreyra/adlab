# Step 14: Object Storage (MinIO) & Backup/Restore System

## Problem Statement

Currently, the laboratory system stores files (PDF reports, signature images, microscopy photos) directly on the application server's filesystem. This approach has several limitations:

1. **Scalability Issues**: Difficult to scale horizontally with multiple application instances
2. **Single Point of Failure**: All files lost if server fails without proper backup
3. **Backup Complexity**: Requires file-level backups alongside database backups
4. **No Versioning**: Previous versions of files are lost when updated
5. **Limited Access Control**: Basic filesystem permissions insufficient for fine-grained control
6. **No Disaster Recovery**: Missing automated backup and restore procedures
7. **Migration Difficulty**: Hard to move between environments or cloud providers

**Solution**: Implement MinIO (S3-compatible object storage) for centralized file management and comprehensive backup/restore strategies.

## Requirements

### Functional Requirements (RF14)

**Storage Requirements:**
- **RF14.1**: Store all application files in object storage (MinIO/S3)
  - Histopathologist signature images
  - Generated PDF reports
  - Microscopy images
  - QR code labels
- **RF14.2**: Maintain file versioning for audit trail
- **RF14.3**: Generate presigned URLs for secure file access
- **RF14.4**: Support both local (MinIO) and cloud (AWS S3) storage backends

**Backup Requirements:**
- **RF14.5**: Automated daily database backups
- **RF14.6**: Continuous file storage replication
- **RF14.7**: Point-in-time recovery capability
- **RF14.8**: Automated backup verification
- **RF14.9**: Backup retention policies (30 days minimum)
- **RF14.10**: Off-site backup storage

**Restore Requirements:**
- **RF14.11**: Database restoration from any backup point
- **RF14.12**: File restoration with version selection
- **RF14.13**: Complete system restoration procedure
- **RF14.14**: Disaster recovery plan documentation

### Non-Functional Requirements

- **Reliability**: 99.9% uptime for storage service
- **Performance**: <500ms file retrieval time
- **Backup Speed**: Complete backup in <30 minutes
- **Restore Speed**: Full system restore in <2 hours
- **Storage Efficiency**: Compression for backups (50%+ reduction)
- **Security**: Encrypted backups, secure access controls

## Current State Analysis

### Files Currently Stored

1. **Signature Images** (`accounts.Histopathologist.signature_image`)
   - Type: `ImageField`
   - Path: `signatures/histopathologists/`
   - Size: ~50KB per image
   - Frequency: Rare (once per histopathologist)

2. **PDF Reports** (`protocols.Report.pdf_path`)
   - Type: `CharField` (file path)
   - Path: `reports/Informe_*.pdf`
   - Size: ~200KB per report
   - Frequency: Daily (multiple reports per day)
   - Critical: Legal documents requiring integrity

3. **Microscopy Images** (`protocols.ReportImage.image_path`)
   - Type: `CharField` (file path)
   - Path: Not yet configured
   - Size: ~2-5MB per image
   - Frequency: Variable (0-10 per report)

4. **QR Code Labels** (from Step 04)
   - Type: Generated PDFs
   - Size: ~10KB per label
   - Frequency: Per protocol reception

### Current Gaps

❌ No `MEDIA_ROOT` or `MEDIA_URL` configured in settings  
❌ PDF files stored with absolute paths instead of relative  
❌ No file versioning or backup strategy  
❌ No disaster recovery plan  
❌ Manual backup procedures not documented  

## Architecture Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Django Application                       │
│                                                                  │
│  ┌──────────────┐       ┌─────────────────┐                    │
│  │   Views      │──────▶│  django-storages│                    │
│  │   (Reports)  │       │   (S3 Backend)  │                    │
│  └──────────────┘       └─────────────────┘                    │
│                                 │                                │
└─────────────────────────────────┼────────────────────────────────┘
                                  │ boto3 API
                                  ▼
                    ┌──────────────────────────┐
                    │    MinIO / AWS S3        │
                    │  (Object Storage)        │
                    │                          │
                    │  Buckets:                │
                    │  - adlab-media          │
                    │  - adlab-backups        │
                    │  - adlab-logs           │
                    └──────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
          ┌──────────────────┐        ┌──────────────────┐
          │  MinIO Backup    │        │  PostgreSQL      │
          │  (Replication)   │        │  (Database)      │
          └──────────────────┘        └──────────────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  ▼
                    ┌──────────────────────────┐
                    │   Backup Service         │
                    │   (Automated Cron)       │
                    │                          │
                    │  - Database dumps        │
                    │  - File sync             │
                    │  - Verification          │
                    └──────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  Off-site Storage        │
                    │  (S3/Glacier/NFS)       │
                    └──────────────────────────┘
```

### Storage Bucket Structure

```
adlab-media/
├── signatures/
│   └── histopathologists/
│       ├── {user_id}/
│       │   └── signature.png
│       └── ...
├── reports/
│   ├── 2024/
│   │   ├── 10/
│   │   │   ├── Informe_HP_24_001_v1.pdf
│   │   │   ├── Informe_HP_24_002_v1.pdf
│   │   │   └── ...
│   │   └── ...
│   └── ...
├── microscopy/
│   └── {report_id}/
│       ├── image_001.jpg
│       ├── image_002.jpg
│       └── ...
└── labels/
    └── {protocol_id}/
        └── label.pdf

adlab-backups/
├── database/
│   ├── daily/
│   │   ├── adlab_db_20241012_020000.sql.gz
│   │   └── ...
│   ├── weekly/
│   │   └── ...
│   └── monthly/
│       └── ...
├── files/
│   └── snapshots/
│       ├── 20241012_020000/
│       └── ...
└── wal_archive/
    └── 000000010000000000000001
    └── ...
```

## Implementation Details

### Phase 1: Add MinIO Service

#### 1.1 Update Docker Compose

Add to `compose.yaml`:

```yaml
services:
  # ... existing services ...

  minio:
    image: "minio/minio:RELEASE.2024-10-02T17-50-41Z"
    profiles: ["minio"]
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: "${MINIO_ROOT_USER:-adlab_admin}"
      MINIO_ROOT_PASSWORD: "${MINIO_ROOT_PASSWORD}"
      MINIO_REGION: "${MINIO_REGION:-us-east-1}"
    ports:
      - "${MINIO_API_PORT:-127.0.0.1:9000}:9000"
      - "${MINIO_CONSOLE_PORT:-127.0.0.1:9001}:9001"
    volumes:
      - "minio_data:/data"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
    restart: "${DOCKER_RESTART_POLICY:-unless-stopped}"
    stop_grace_period: "3s"
    networks:
      - default

  # MinIO Client (mc) for administration
  minio-client:
    image: "minio/mc:RELEASE.2024-10-02T08-55-05Z"
    profiles: ["minio-admin"]
    depends_on:
      - minio
    entrypoint: /bin/sh
    volumes:
      - "./bin:/scripts"
    networks:
      - default

volumes:
  minio_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: "${MINIO_DATA_PATH:-./data/minio}"
```

#### 1.2 Environment Configuration

Add to `.env`:

```bash
# MinIO Configuration
MINIO_ROOT_USER=adlab_admin
MINIO_ROOT_PASSWORD=your_secure_password_min_8_chars
MINIO_REGION=us-east-1
MINIO_DATA_PATH=./data/minio

# Storage Backend Selection
USE_S3_STORAGE=true  # false for local filesystem
AWS_ACCESS_KEY_ID=adlab_admin
AWS_SECRET_ACCESS_KEY=your_secure_password_min_8_chars
AWS_STORAGE_BUCKET_NAME=adlab-media
AWS_S3_ENDPOINT_URL=http://minio:9000  # Empty for AWS S3
AWS_S3_REGION_NAME=us-east-1

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_S3_BUCKET=adlab-backups
BACKUP_SCHEDULE_DATABASE="0 2 * * *"  # 2 AM daily
BACKUP_SCHEDULE_FILES="0 3 * * *"     # 3 AM daily
BACKUP_SCHEDULE_COMPLETE="0 4 * * 0"  # 4 AM Sunday
```

#### 1.3 Initialize MinIO Buckets

Create `bin/minio-init`:

```bash
#!/bin/bash
# Initialize MinIO buckets and policies

set -euo pipefail

MINIO_HOST="${MINIO_HOST:-minio:9000}"
MINIO_ALIAS="adlab"

echo "🔧 Configuring MinIO client..."
mc alias set $MINIO_ALIAS http://$MINIO_HOST $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD

echo "📦 Creating buckets..."
mc mb --ignore-existing ${MINIO_ALIAS}/adlab-media
mc mb --ignore-existing ${MINIO_ALIAS}/adlab-backups
mc mb --ignore-existing ${MINIO_ALIAS}/adlab-logs

echo "🔒 Setting bucket policies..."
# Private bucket for sensitive medical data
mc anonymous set none ${MINIO_ALIAS}/adlab-media
mc anonymous set none ${MINIO_ALIAS}/adlab-backups

echo "📝 Enabling versioning..."
mc version enable ${MINIO_ALIAS}/adlab-media
mc version enable ${MINIO_ALIAS}/adlab-backups

echo "⏰ Setting lifecycle policies..."
# Auto-delete old versions after 90 days
cat > /tmp/lifecycle.json <<EOF
{
  "Rules": [
    {
      "ID": "DeleteOldVersions",
      "Status": "Enabled",
      "Filter": {
        "Prefix": ""
      },
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 90
      }
    }
  ]
}
EOF
mc ilm import ${MINIO_ALIAS}/adlab-media < /tmp/lifecycle.json

echo "✅ MinIO initialized successfully!"
echo ""
echo "📊 Bucket Status:"
mc admin info ${MINIO_ALIAS}
```

Make executable:
```bash
chmod +x bin/minio-init
```

### Phase 2: Django Storage Integration

#### 2.1 Install Dependencies

Add to `pyproject.toml`:

```toml
dependencies = [
  # ... existing ...
  "django-storages[s3]==1.14.4",
  "boto3==1.35.89",
]
```

Install:
```bash
docker compose exec web uv sync
```

#### 2.2 Update Django Settings

Add to `src/config/settings.py`:

```python
# Media files (User uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "..", "media")

# Storage Configuration
USE_S3_STORAGE = bool(strtobool(os.getenv("USE_S3_STORAGE", "false")))

if USE_S3_STORAGE:
    # MinIO/S3 Configuration
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "adlab-media")
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")  # None for AWS S3
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "us-east-1")
    
    # S3 Configuration
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',  # 1 day cache
    }
    AWS_DEFAULT_ACL = None  # Use bucket policy
    AWS_QUERYSTRING_AUTH = True  # Use presigned URLs
    AWS_QUERYSTRING_EXPIRE = 3600  # URLs expire in 1 hour
    AWS_S3_FILE_OVERWRITE = False  # Prevent overwriting
    AWS_S3_VERIFY = True  # Verify SSL certificates
    AWS_S3_USE_SSL = True  # Use HTTPS (set False for local MinIO without SSL)
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    
    # Custom domain (if using CloudFront or similar)
    if AWS_S3_ENDPOINT_URL:
        AWS_S3_CUSTOM_DOMAIN = None  # Use presigned URLs
    
    # Storage backends
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    # For production, you might want separate buckets for static files:
    # STATICFILES_STORAGE = 'config.storage_backends.StaticStorage'
else:
    # Local file storage (development)
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755
```

#### 2.3 Create Custom Storage Backends (Optional)

Create `src/config/storage_backends.py`:

```python
"""
Custom storage backends for different file types.
"""
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """Storage for user-uploaded media files."""
    location = 'media'
    file_overwrite = False
    default_acl = None


class ReportStorage(S3Boto3Storage):
    """Storage for generated PDF reports."""
    location = 'reports'
    file_overwrite = False
    default_acl = None
    
    def get_available_name(self, name, max_length=None):
        """Generate filename with date hierarchy."""
        from datetime import datetime
        date = datetime.now()
        name_parts = name.split('/')
        filename = name_parts[-1]
        new_name = f"{date.year}/{date.month:02d}/{filename}"
        return super().get_available_name(new_name, max_length)


class SignatureStorage(S3Boto3Storage):
    """Storage for histopathologist signatures."""
    location = 'signatures/histopathologists'
    file_overwrite = True  # Allow signature updates
    default_acl = None


class StaticStorage(S3Boto3Storage):
    """Storage for static files (CSS, JS)."""
    location = 'static'
    default_acl = 'public-read'
    querystring_auth = False  # Public access
```

#### 2.4 Update Models to Use Storage

Update `src/accounts/models.py`:

```python
from config.storage_backends import SignatureStorage

class Histopathologist(models.Model):
    # ... existing fields ...
    
    signature_image = models.ImageField(
        _("firma digital"),
        upload_to="",  # Empty, handled by storage backend
        storage=SignatureStorage() if settings.USE_S3_STORAGE else None,
        blank=True,
        null=True,
        help_text=_("Imagen de la firma para incluir en informes"),
    )
```

#### 2.5 Update Report PDF Generation

Update `src/protocols/views_reports.py`:

```python
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from config.storage_backends import ReportStorage

def report_finalize_view(request, pk):
    """Finalize report and generate PDF."""
    # ... permission checks ...
    
    try:
        with transaction.atomic():
            # Generate PDF
            pdf_buffer, pdf_hash = generate_report_pdf(report)
            
            # Generate filename
            pdf_filename = report.generate_pdf_filename()
            
            # Use custom storage backend if available
            if settings.USE_S3_STORAGE:
                storage = ReportStorage()
            else:
                storage = default_storage
            
            # Save PDF
            saved_path = storage.save(
                pdf_filename,
                ContentFile(pdf_buffer.getvalue())
            )
            
            # Update report
            report.pdf_path = saved_path
            report.pdf_hash = pdf_hash
            report.finalize()
            
            messages.success(
                request,
                _("Informe finalizado exitosamente. El PDF ha sido generado.")
            )
            return redirect("protocols:report_detail", pk=report.pk)
            
    except Exception as e:
        logger.error(f"Error finalizing report {report.pk}: {e}")
        messages.error(
            request,
            _("Error al finalizar el informe: %(error)s") % {"error": str(e)}
        )
        return redirect("protocols:report_edit", pk=report.pk)


def report_pdf_view(request, pk):
    """View/download report PDF."""
    report = get_object_or_404(Report, pk=pk)
    
    # Check permissions...
    
    if not report.pdf_path:
        messages.error(
            request,
            _("El PDF del informe no está disponible.")
        )
        return redirect("protocols:report_detail", pk=report.pk)
    
    try:
        # Get storage backend
        if settings.USE_S3_STORAGE:
            storage = ReportStorage()
        else:
            storage = default_storage
        
        # Check if file exists
        if not storage.exists(report.pdf_path):
            raise FileNotFoundError("PDF file not found")
        
        # Open file
        pdf_file = storage.open(report.pdf_path, 'rb')
        
        # Return response
        response = FileResponse(
            pdf_file,
            content_type="application/pdf",
            as_attachment=False,
            filename=report.generate_pdf_filename(),
        )
        return response
        
    except Exception as e:
        logger.error(f"Error serving PDF for report {report.pk}: {e}")
        messages.error(
            request,
            _("Error al cargar el PDF del informe.")
        )
        return redirect("protocols:report_detail", pk=report.pk)
```

### Phase 3: Backup System Implementation

#### 3.1 Database Backup Script

Create `bin/backup-database`:

```bash
#!/bin/bash
# Automated PostgreSQL backup script

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/database}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_FOLDER=$(date +%Y/%m)
BACKUP_FILE="adlab_db_${TIMESTAMP}.sql.gz"
BACKUP_PATH="${BACKUP_DIR}/daily/${DATE_FOLDER}"

# Ensure backup directory exists
mkdir -p "$BACKUP_PATH"

echo "📦 Starting database backup..."
echo "   Target: ${BACKUP_PATH}/${BACKUP_FILE}"

# Perform backup with custom format (for faster restore)
docker compose exec -T postgres pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --format=custom \
    --compress=9 \
    --verbose \
    2>&1 | gzip > "${BACKUP_PATH}/${BACKUP_FILE}"

# Verify backup
if [ -f "${BACKUP_PATH}/${BACKUP_FILE}" ]; then
    SIZE=$(du -h "${BACKUP_PATH}/${BACKUP_FILE}" | cut -f1)
    echo "✅ Backup created: ${BACKUP_FILE} (${SIZE})"
    
    # Create checksum
    cd "${BACKUP_PATH}"
    sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"
    echo "🔐 Checksum created"
else
    echo "❌ Backup failed!"
    exit 1
fi

# Upload to MinIO
if [ "${USE_S3_STORAGE:-false}" = "true" ]; then
    echo "☁️  Uploading to MinIO..."
    mc cp "${BACKUP_PATH}/${BACKUP_FILE}" \
        adlab/adlab-backups/database/daily/${DATE_FOLDER}/${BACKUP_FILE}
    mc cp "${BACKUP_PATH}/${BACKUP_FILE}.sha256" \
        adlab/adlab-backups/database/daily/${DATE_FOLDER}/${BACKUP_FILE}.sha256
    echo "✅ Backup uploaded to object storage"
fi

# Cleanup old backups
echo "🧹 Cleaning up old backups (>${RETENTION_DAYS} days)..."
find "$BACKUP_DIR" -name "adlab_db_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
find "$BACKUP_DIR" -name "*.sha256" -mtime +${RETENTION_DAYS} -delete

# Weekly and monthly backups
WEEK_DAY=$(date +%u)
MONTH_DAY=$(date +%d)

if [ "$WEEK_DAY" -eq 7 ]; then
    # Sunday - create weekly backup
    WEEKLY_PATH="${BACKUP_DIR}/weekly/${DATE_FOLDER}"
    mkdir -p "$WEEKLY_PATH"
    cp "${BACKUP_PATH}/${BACKUP_FILE}" "$WEEKLY_PATH/"
    cp "${BACKUP_PATH}/${BACKUP_FILE}.sha256" "$WEEKLY_PATH/"
    echo "📅 Weekly backup created"
fi

if [ "$MONTH_DAY" -eq 1 ]; then
    # First day of month - create monthly backup
    MONTHLY_PATH="${BACKUP_DIR}/monthly/$(date +%Y)"
    mkdir -p "$MONTHLY_PATH"
    cp "${BACKUP_PATH}/${BACKUP_FILE}" "$MONTHLY_PATH/"
    cp "${BACKUP_PATH}/${BACKUP_FILE}.sha256" "$MONTHLY_PATH/"
    echo "📅 Monthly backup created"
fi

echo "✅ Database backup completed successfully!"
```

#### 3.2 File Storage Backup Script

Create `bin/backup-files`:

```bash
#!/bin/bash
# Backup files from MinIO to local storage or remote

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups/files}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BUCKET="adlab-media"
SNAPSHOT_DIR="${BACKUP_DIR}/snapshots/${TIMESTAMP}"

mkdir -p "$SNAPSHOT_DIR"

echo "📁 Starting file backup from MinIO..."
echo "   Source: minio/${BUCKET}"
echo "   Target: ${SNAPSHOT_DIR}"

# Mirror bucket to local storage (preserves metadata)
mc mirror --preserve --remove \
    adlab/${BUCKET} \
    "${SNAPSHOT_DIR}/"

# Verify file count
FILE_COUNT=$(find "$SNAPSHOT_DIR" -type f | wc -l)
echo "📊 Backed up ${FILE_COUNT} files"

# Create compressed archive
ARCHIVE_NAME="${BUCKET}_${TIMESTAMP}.tar.gz"
echo "🗜️  Creating compressed archive..."
tar -czf "${BACKUP_DIR}/${ARCHIVE_NAME}" \
    -C "${BACKUP_DIR}/snapshots" \
    "${TIMESTAMP}"

# Create checksum
cd "$BACKUP_DIR"
sha256sum "${ARCHIVE_NAME}" > "${ARCHIVE_NAME}.sha256"

# Remove uncompressed snapshot
rm -rf "$SNAPSHOT_DIR"

ARCHIVE_SIZE=$(du -h "${BACKUP_DIR}/${ARCHIVE_NAME}" | cut -f1)
echo "✅ Archive created: ${ARCHIVE_NAME} (${ARCHIVE_SIZE})"

# Upload to backup bucket
echo "☁️  Uploading to backup bucket..."
mc cp "${BACKUP_DIR}/${ARCHIVE_NAME}" \
    adlab/adlab-backups/files/${ARCHIVE_NAME}
mc cp "${BACKUP_DIR}/${ARCHIVE_NAME}.sha256" \
    adlab/adlab-backups/files/${ARCHIVE_NAME}.sha256

# Cleanup old local archives
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
echo "🧹 Cleaning up old archives (>${RETENTION_DAYS} days)..."
find "$BACKUP_DIR" -name "${BUCKET}_*.tar.gz" -mtime +${RETENTION_DAYS} -delete

echo "✅ File backup completed successfully!"
```

#### 3.3 Complete System Backup Script

Create `bin/backup-complete`:

```bash
#!/bin/bash
# Complete system backup (database + files + config)

set -euo pipefail

BACKUP_ROOT="${BACKUP_ROOT:-/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/complete/${TIMESTAMP}"

mkdir -p "$BACKUP_DIR"

echo "🔄 ===== COMPLETE SYSTEM BACKUP ====="
echo "   Timestamp: ${TIMESTAMP}"
echo "   Location: ${BACKUP_DIR}"
echo ""

# 1. Backup database
echo "📦 [1/5] Backing up database..."
./bin/backup-database
DB_BACKUP=$(find /backups/database/daily -name "adlab_db_*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -f2- -d" ")
cp "$DB_BACKUP" "${BACKUP_DIR}/database.sql.gz"
echo "✅ Database backup copied"
echo ""

# 2. Backup files from MinIO
echo "📁 [2/5] Backing up files from MinIO..."
mc mirror --preserve adlab/adlab-media "${BACKUP_DIR}/media"
echo "✅ Files backed up"
echo ""

# 3. Backup configuration
echo "⚙️  [3/5] Backing up configuration..."
mkdir -p "${BACKUP_DIR}/config"
cp .env "${BACKUP_DIR}/config/.env.backup"
cp compose.yaml "${BACKUP_DIR}/config/compose.yaml"
cp -r bin "${BACKUP_DIR}/config/"
echo "✅ Configuration backed up"
echo ""

# 4. Create metadata
echo "📝 [4/5] Creating backup metadata..."
cat > "${BACKUP_DIR}/backup_info.json" <<EOF
{
  "backup_date": "$(date -Iseconds)",
  "backup_type": "complete",
  "database": "${POSTGRES_DB}",
  "minio_bucket": "adlab-media",
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
  "hostname": "$(hostname)",
  "user": "$(whoami)"
}
EOF

# System info
docker compose version > "${BACKUP_DIR}/system_info.txt"
docker compose ps >> "${BACKUP_DIR}/system_info.txt"
echo "✅ Metadata created"
echo ""

# 5. Create archive
echo "🗜️  [5/5] Creating compressed archive..."
ARCHIVE_NAME="adlab_complete_${TIMESTAMP}.tar.gz"
tar -czf "${BACKUP_ROOT}/${ARCHIVE_NAME}" \
    -C "${BACKUP_ROOT}/complete" \
    "${TIMESTAMP}"

# Checksum
cd "$BACKUP_ROOT"
sha256sum "${ARCHIVE_NAME}" > "${ARCHIVE_NAME}.sha256"

# Upload to MinIO
mc cp "${ARCHIVE_NAME}" adlab/adlab-backups/complete/
mc cp "${ARCHIVE_NAME}.sha256" adlab/adlab-backups/complete/

# Cleanup
rm -rf "$BACKUP_DIR"

ARCHIVE_SIZE=$(du -h "${BACKUP_ROOT}/${ARCHIVE_NAME}" | cut -f1)
echo ""
echo "✅ ===== COMPLETE BACKUP FINISHED ====="
echo "   Archive: ${ARCHIVE_NAME}"
echo "   Size: ${ARCHIVE_SIZE}"
echo "   Location: ${BACKUP_ROOT}/${ARCHIVE_NAME}"
echo "   Remote: adlab/adlab-backups/complete/${ARCHIVE_NAME}"
```

#### 3.4 Automated Backup Service

Create `bin/backup-scheduler`:

```bash
#!/bin/bash
# Backup scheduler using cron

cat > /etc/cron.d/adlab-backup << 'EOF'
# AdLab Automated Backup Schedule
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAILTO=""

# Daily database backup at 2:00 AM
0 2 * * * root /app/bin/backup-database >> /var/log/backup.log 2>&1

# Hourly file sync
0 * * * * root /app/bin/backup-files >> /var/log/backup.log 2>&1

# Weekly complete backup on Sunday at 3:00 AM
0 3 * * 0 root /app/bin/backup-complete >> /var/log/backup.log 2>&1

# Monthly backup verification on 1st at 4:00 AM
0 4 1 * * root /app/bin/verify-backups >> /var/log/backup.log 2>&1
EOF

chmod 0644 /etc/cron.d/adlab-backup
crontab /etc/cron.d/adlab-backup

echo "✅ Backup schedule configured"
crontab -l
```

Add backup service to `compose.yaml`:

```yaml
backup:
  <<: *default-app
  profiles: ["backup"]
  command: crond -f -l 2
  volumes:
    - "./bin:/app/bin"
    - "./backups:/backups"
    - "/var/run/docker.sock:/var/run/docker.sock"
  environment:
    BACKUP_ENABLED: "true"
    BACKUP_RETENTION_DAYS: "${BACKUP_RETENTION_DAYS:-30}"
  restart: "${DOCKER_RESTART_POLICY:-unless-stopped}"
```

### Phase 4: Restore Procedures

#### 4.1 Database Restore Script

Create `bin/restore-database`:

```bash
#!/bin/bash
# Restore database from backup

set -euo pipefail

function show_usage() {
    echo "Usage: $0 <backup_file.sql.gz> [--force]"
    echo ""
    echo "Available backups:"
    echo "  Local:"
    find /backups/database -name "*.sql.gz" -type f -printf "    %TY-%Tm-%Td %TH:%TM  %p\n" | sort -r | head -10
    echo ""
    echo "  Remote (MinIO):"
    mc ls --recursive adlab/adlab-backups/database/ | tail -10
    echo ""
    exit 1
}

if [ -z "$1" ]; then
    show_usage
fi

BACKUP_FILE="$1"
FORCE_RESTORE="${2:-}"

# Verify backup file
if [ ! -f "$BACKUP_FILE" ]; then
    # Try to fetch from MinIO
    if [[ "$BACKUP_FILE" == adlab/* ]]; then
        echo "📥 Downloading from MinIO..."
        LOCAL_FILE="/tmp/$(basename $BACKUP_FILE)"
        mc cp "$BACKUP_FILE" "$LOCAL_FILE"
        BACKUP_FILE="$LOCAL_FILE"
    else
        echo "❌ Backup file not found: $BACKUP_FILE"
        exit 1
    fi
fi

# Verify checksum if available
if [ -f "${BACKUP_FILE}.sha256" ]; then
    echo "🔐 Verifying checksum..."
    cd "$(dirname $BACKUP_FILE)"
    sha256sum -c "$(basename ${BACKUP_FILE}).sha256"
    echo "✅ Checksum verified"
fi

# Confirmation
if [ "$FORCE_RESTORE" != "--force" ]; then
    echo "⚠️  WARNING: This will OVERWRITE the current database!"
    echo "   Database: ${POSTGRES_DB}"
    echo "   Backup: $(basename $BACKUP_FILE)"
    echo "   Size: $(du -h $BACKUP_FILE | cut -f1)"
    echo ""
    read -p "Type 'yes' to continue: " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Restoration cancelled."
        exit 0
    fi
fi

# Stop application services
echo "🛑 Stopping application services..."
docker compose stop web worker beat

# Wait for connections to close
sleep 5

# Terminate existing connections
echo "🔌 Terminating database connections..."
docker compose exec -T postgres psql -U "$POSTGRES_USER" -d postgres <<SQL
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '${POSTGRES_DB}'
  AND pid <> pg_backend_pid();
SQL

# Drop and recreate database
echo "🗑️  Dropping existing database..."
docker compose exec -T postgres psql -U "$POSTGRES_USER" -d postgres <<SQL
DROP DATABASE IF EXISTS ${POSTGRES_DB};
CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER};
SQL

# Restore backup
echo "♻️  Restoring database from backup..."
gunzip -c "$BACKUP_FILE" | docker compose exec -T postgres pg_restore \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --no-owner \
    --no-acl \
    --verbose \
    2>&1 | grep -v "^pg_restore: "

# Run migrations (in case backup is from older version)
echo "🔄 Running migrations..."
docker compose run --rm web python manage.py migrate --no-input

# Restart services
echo "▶️  Starting application services..."
docker compose start web worker beat

# Wait for services
sleep 5

# Verify
echo "🔍 Verifying restoration..."
docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT COUNT(*) FROM django_migrations;"

echo ""
echo "✅ Database restored successfully!"
echo "   From: $(basename $BACKUP_FILE)"
echo "   To: ${POSTGRES_DB}"
```

#### 4.2 Files Restore Script

Create `bin/restore-files`:

```bash
#!/bin/bash
# Restore files to MinIO

set -euo pipefail

function show_usage() {
    echo "Usage: $0 <backup_archive.tar.gz|directory> [--force]"
    echo ""
    echo "Available backups:"
    echo "  Local:"
    find /backups/files -name "*.tar.gz" -type f -printf "    %TY-%Tm-%Td  %p\n" | sort -r | head -10
    echo ""
    echo "  Remote (MinIO):"
    mc ls adlab/adlab-backups/files/ | tail -10
    echo ""
    exit 1
}

if [ -z "$1" ]; then
    show_usage
fi

BACKUP_SOURCE="$1"
FORCE_RESTORE="${2:-}"
TEMP_DIR="/tmp/restore_$$"

# Confirmation
if [ "$FORCE_RESTORE" != "--force" ]; then
    echo "⚠️  WARNING: This will OVERWRITE files in MinIO!"
    echo "   Bucket: adlab-media"
    echo "   Source: $BACKUP_SOURCE"
    echo ""
    read -p "Type 'yes' to continue: " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Restoration cancelled."
        exit 0
    fi
fi

mkdir -p "$TEMP_DIR"

# Extract or use directory
if [ -f "$BACKUP_SOURCE" ]; then
    echo "📦 Extracting backup archive..."
    tar -xzf "$BACKUP_SOURCE" -C "$TEMP_DIR"
    RESTORE_DIR="$TEMP_DIR"
elif [ -d "$BACKUP_SOURCE" ]; then
    RESTORE_DIR="$BACKUP_SOURCE"
else
    echo "❌ Invalid backup source"
    exit 1
fi

# Upload files to MinIO
echo "☁️  Uploading files to MinIO..."
mc mirror --overwrite --preserve \
    "$RESTORE_DIR" \
    adlab/adlab-media/

# Verify
FILE_COUNT=$(mc ls --recursive adlab/adlab-media | wc -l)
echo "📊 Restored ${FILE_COUNT} files"

# Cleanup
if [ -f "$BACKUP_SOURCE" ]; then
    rm -rf "$TEMP_DIR"
fi

echo "✅ Files restored successfully!"
```

#### 4.3 Complete System Restore Script

Create `bin/restore-complete`:

```bash
#!/bin/bash
# Complete system restoration

set -euo pipefail

function show_usage() {
    echo "Usage: $0 <complete_backup.tar.gz> [--force]"
    echo ""
    echo "Available complete backups:"
    find /backups/complete -name "adlab_complete_*.tar.gz" -type f -printf "    %TY-%Tm-%Td  %p\n" | sort -r | head -10
    echo ""
    mc ls adlab/adlab-backups/complete/ | tail -10
    echo ""
    exit 1
}

if [ -z "$1" ]; then
    show_usage
fi

BACKUP_FILE="$1"
FORCE_RESTORE="${2:-}"
TEMP_DIR="/tmp/complete_restore_$$"

# Confirmation
if [ "$FORCE_RESTORE" != "--force" ]; then
    echo "⚠️  WARNING: COMPLETE SYSTEM RESTORATION"
    echo "   This will restore:"
    echo "   - Database"
    echo "   - All files"
    echo "   - Configuration"
    echo ""
    echo "   Backup: $(basename $BACKUP_FILE)"
    echo ""
    read -p "Type 'YES' (uppercase) to continue: " confirm
    
    if [ "$confirm" != "YES" ]; then
        echo "Restoration cancelled."
        exit 0
    fi
fi

# Extract complete backup
echo "📦 Extracting complete backup..."
mkdir -p "$TEMP_DIR"
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Find extracted directory
BACKUP_DIR=$(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d)

# Show backup info
if [ -f "${BACKUP_DIR}/backup_info.json" ]; then
    echo "📋 Backup Information:"
    cat "${BACKUP_DIR}/backup_info.json"
    echo ""
fi

# Stop all services
echo "🛑 Stopping all services..."
docker compose down

# 1. Restore database
echo "📦 [1/3] Restoring database..."
./bin/restore-database "${BACKUP_DIR}/database.sql.gz" --force

# 2. Restore files
echo "📁 [2/3] Restoring files..."
./bin/restore-files "${BACKUP_DIR}/media" --force

# 3. Restore configuration (optional, manual review recommended)
echo "⚙️  [3/3] Configuration files available at:"
echo "   ${BACKUP_DIR}/config/"
echo "   Review and manually restore if needed."

# Cleanup
rm -rf "$TEMP_DIR"

# Start services
echo "▶️  Starting all services..."
docker compose up -d

echo ""
echo "✅ Complete system restoration finished!"
echo "   Please verify the system is working correctly."
```

### Phase 5: Backup Verification

#### 5.1 Verification Script

Create `bin/verify-backups`:

```bash
#!/bin/bash
# Verify backup integrity and completeness

set -euo pipefail

REPORT_FILE="/var/log/backup_verification_$(date +%Y%m%d).txt"

echo "====================================" | tee "$REPORT_FILE"
echo "BACKUP VERIFICATION REPORT" | tee -a "$REPORT_FILE"
echo "Generated: $(date)" | tee -a "$REPORT_FILE"
echo "====================================" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# 1. Check database backups
echo "📦 DATABASE BACKUPS" | tee -a "$REPORT_FILE"
echo "-----------------------------------" | tee -a "$REPORT_FILE"

# Recent backups
RECENT_DB=$(find /backups/database/daily -name "*.sql.gz" -mtime -7 -type f)
if [ -z "$RECENT_DB" ]; then
    echo "❌ No database backups in last 7 days!" | tee -a "$REPORT_FILE"
else
    echo "✅ Recent database backups found:" | tee -a "$REPORT_FILE"
    echo "$RECENT_DB" | while read file; do
        size=$(du -h "$file" | cut -f1)
        date=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$file" 2>/dev/null || stat -c "%y" "$file")
        
        # Verify checksum
        if [ -f "${file}.sha256" ]; then
            cd "$(dirname $file)"
            if sha256sum -c "$(basename ${file}).sha256" &>/dev/null; then
                echo "  ✓ $file ($size) - $date [checksum OK]" | tee -a "$REPORT_FILE"
            else
                echo "  ✗ $file ($size) - $date [checksum FAILED]" | tee -a "$REPORT_FILE"
            fi
        else
            echo "  ? $file ($size) - $date [no checksum]" | tee -a "$REPORT_FILE"
        fi
    done
fi
echo "" | tee -a "$REPORT_FILE"

# 2. Check MinIO storage
echo "☁️  MINIO STORAGE" | tee -a "$REPORT_FILE"
echo "-----------------------------------" | tee -a "$REPORT_FILE"

# Bucket status
mc du adlab/adlab-media | tee -a "$REPORT_FILE"
mc du adlab/adlab-backups | tee -a "$REPORT_FILE"

# File count
MEDIA_FILES=$(mc ls --recursive adlab/adlab-media | wc -l)
echo "  Media files: ${MEDIA_FILES}" | tee -a "$REPORT_FILE"

# Test file access
echo "  Testing file access..." | tee -a "$REPORT_FILE"
SAMPLE_FILE=$(mc ls --recursive adlab/adlab-media | head -1 | awk '{print $NF}')
if [ -n "$SAMPLE_FILE" ]; then
    if mc stat "adlab/adlab-media/${SAMPLE_FILE}" &>/dev/null; then
        echo "  ✅ File access working" | tee -a "$REPORT_FILE"
    else
        echo "  ❌ File access failed!" | tee -a "$REPORT_FILE"
    fi
else
    echo "  ⚠️  No files to test" | tee -a "$REPORT_FILE"
fi
echo "" | tee -a "$REPORT_FILE"

# 3. Check backup storage
echo "💾 BACKUP STORAGE" | tee -a "$REPORT_FILE"
echo "-----------------------------------" | tee -a "$REPORT_FILE"

BACKUP_SIZE=$(mc du adlab/adlab-backups | awk '{print $1}')
echo "  Total backup size: ${BACKUP_SIZE}" | tee -a "$REPORT_FILE"

# Database backups in MinIO
DB_BACKUPS=$(mc ls --recursive adlab/adlab-backups/database/ | wc -l)
echo "  Database backups: ${DB_BACKUPS}" | tee -a "$REPORT_FILE"

# File backups in MinIO
FILE_BACKUPS=$(mc ls adlab/adlab-backups/files/ | wc -l)
echo "  File backups: ${FILE_BACKUPS}" | tee -a "$REPORT_FILE"

# Complete backups
COMPLETE_BACKUPS=$(mc ls adlab/adlab-backups/complete/ | wc -l)
echo "  Complete backups: ${COMPLETE_BACKUPS}" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# 4. Test restore (dry-run)
echo "🔄 RESTORE TEST (DRY-RUN)" | tee -a "$REPORT_FILE"
echo "-----------------------------------" | tee -a "$REPORT_FILE"

# Get latest backup
LATEST_BACKUP=$(find /backups/database/daily -name "*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -f2- -d" ")

if [ -n "$LATEST_BACKUP" ]; then
    echo "  Latest backup: $(basename $LATEST_BACKUP)" | tee -a "$REPORT_FILE"
    
    # Test decompression
    if gunzip -t "$LATEST_BACKUP" 2>/dev/null; then
        echo "  ✅ Backup file integrity OK" | tee -a "$REPORT_FILE"
    else
        echo "  ❌ Backup file corrupted!" | tee -a "$REPORT_FILE"
    fi
else
    echo "  ❌ No backups found!" | tee -a "$REPORT_FILE"
fi
echo "" | tee -a "$REPORT_FILE"

# 5. Health check
echo "🏥 SYSTEM HEALTH" | tee -a "$REPORT_FILE"
echo "-----------------------------------" | tee -a "$REPORT_FILE"

# Database connection
if docker compose exec -T postgres pg_isready -U "$POSTGRES_USER" &>/dev/null; then
    echo "  ✅ Database: Connected" | tee -a "$REPORT_FILE"
else
    echo "  ❌ Database: Not reachable" | tee -a "$REPORT_FILE"
fi

# MinIO health
if mc admin info adlab &>/dev/null; then
    echo "  ✅ MinIO: Healthy" | tee -a "$REPORT_FILE"
else
    echo "  ❌ MinIO: Not reachable" | tee -a "$REPORT_FILE"
fi

# Disk space
DISK_USAGE=$(df -h /backups | tail -1 | awk '{print $5}')
echo "  Backup disk usage: ${DISK_USAGE}" | tee -a "$REPORT_FILE"

if [ "${DISK_USAGE%?}" -gt 80 ]; then
    echo "  ⚠️  Warning: Disk usage above 80%" | tee -a "$REPORT_FILE"
fi
echo "" | tee -a "$REPORT_FILE"

# Summary
echo "====================================" | tee -a "$REPORT_FILE"
echo "VERIFICATION COMPLETE" | tee -a "$REPORT_FILE"
echo "Report saved to: $REPORT_FILE" | tee -a "$REPORT_FILE"
echo "====================================" | tee -a "$REPORT_FILE"

# Send email notification (if configured)
if [ -n "${BACKUP_NOTIFICATION_EMAIL:-}" ]; then
    echo "Sending notification email to: $BACKUP_NOTIFICATION_EMAIL"
    # Implement email sending logic here
fi
```

Make all scripts executable:
```bash
chmod +x bin/backup-*
chmod +x bin/restore-*
chmod +x bin/verify-backups
chmod +x bin/minio-init
```

## Testing Approach

### Unit Tests

Test storage backend integration:

```python
# src/protocols/tests_storage.py
from django.test import TestCase, override_settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

class StorageBackendTest(TestCase):
    """Test storage backend functionality."""
    
    @override_settings(USE_S3_STORAGE=True)
    def test_save_file_to_s3(self):
        """Test saving file to S3/MinIO."""
        content = ContentFile(b"test content")
        path = default_storage.save("test/file.txt", content)
        self.assertTrue(default_storage.exists(path))
        
    def test_generate_presigned_url(self):
        """Test presigned URL generation."""
        # Implementation
        pass
```

### Integration Tests

```python
# src/protocols/tests_backup.py
import subprocess
from django.test import TestCase

class BackupRestoreTest(TestCase):
    """Test backup and restore procedures."""
    
    def test_database_backup(self):
        """Test database backup script."""
        result = subprocess.run(
            ["./bin/backup-database"],
            capture_output=True
        )
        self.assertEqual(result.returncode, 0)
        
    def test_database_restore(self):
        """Test database restore script."""
        # Create test backup
        # Restore from backup
        # Verify data integrity
        pass
```

### Manual Testing Checklist

```markdown
## Pre-Implementation Testing

- [ ] MinIO service starts successfully
- [ ] Buckets are created correctly
- [ ] Django can connect to MinIO
- [ ] Files upload successfully
- [ ] Files download successfully
- [ ] Presigned URLs work correctly

## Backup Testing

- [ ] Database backup runs successfully
- [ ] Database backup uploads to MinIO
- [ ] File backup creates archive
- [ ] File backup uploads to MinIO
- [ ] Complete backup includes all components
- [ ] Backup checksums are created
- [ ] Old backups are cleaned up correctly

## Restore Testing

- [ ] Database restore from backup works
- [ ] File restore from backup works
- [ ] Complete system restore works
- [ ] Restored data is correct
- [ ] Application works after restore

## Production Readiness

- [ ] Automated backups run on schedule
- [ ] Backup notifications work
- [ ] Backup verification passes
- [ ] Disk space monitoring works
- [ ] Documentation is complete
- [ ] Team is trained on restore procedures
```

## Production Deployment

### Pre-Deployment Checklist

```bash
# 1. Update dependencies
docker compose exec web uv sync

# 2. Run migrations
docker compose exec web python manage.py migrate

# 3. Start MinIO
docker compose --profile minio up -d

# 4. Initialize MinIO
docker compose exec web ./bin/minio-init

# 5. Test storage
docker compose exec web python manage.py shell <<EOF
from django.core.files.storage import default_storage
default_storage.save("test.txt", ContentFile(b"test"))
assert default_storage.exists("test.txt")
print("✅ Storage working!")
EOF

# 6. Run backup test
./bin/backup-database
./bin/backup-files

# 7. Verify backups
./bin/verify-backups

# 8. Start backup service
docker compose --profile backup up -d

# 9. Update environment
# Set USE_S3_STORAGE=true in production .env

# 10. Restart application
docker compose restart web worker
```

### Monitoring & Alerts

Set up monitoring for:

1. **Backup Success/Failure**
   - Monitor backup logs
   - Alert on failed backups
   - Track backup duration

2. **Storage Health**
   - Monitor MinIO uptime
   - Track storage usage
   - Alert on high disk usage

3. **Restore Tests**
   - Weekly automated restore test
   - Verify data integrity
   - Document restore time

### Disaster Recovery Plan

#### RTO (Recovery Time Objective): 2 hours
#### RPO (Recovery Point Objective): 1 hour

**Scenario 1: Database Corruption**
```bash
# 1. Stop application
docker compose stop web worker

# 2. Restore database from latest backup
./bin/restore-database /backups/database/daily/.../latest.sql.gz --force

# 3. Restart application
docker compose start web worker

# Estimated time: 15-30 minutes
```

**Scenario 2: File Storage Loss**
```bash
# 1. Stop application
docker compose stop web

# 2. Restore files from backup
./bin/restore-files /backups/files/latest.tar.gz --force

# 3. Restart application
docker compose start web

# Estimated time: 30-60 minutes
```

**Scenario 3: Complete System Failure**
```bash
# 1. Restore from complete backup
./bin/restore-complete /backups/complete/latest.tar.gz --force

# 2. Verify system
docker compose ps
./bin/verify-backups

# Estimated time: 1-2 hours
```

## Cost Analysis

### Storage Costs (Monthly)

**MinIO (Self-Hosted)**:
- Server: $0 (uses existing infrastructure)
- Disk (500GB): ~$20-40 per month
- Maintenance: Minimal

**AWS S3 (Alternative)**:
- Storage (500GB): ~$11.50 per month
- Requests (100K): ~$0.50 per month
- Data transfer: ~$9 per 100GB

**Total estimated cost**: $20-40/month (self-hosted) vs $20-50/month (cloud)

### Time Savings

- Manual backup time saved: ~2 hours/week
- Faster disaster recovery: ~4 hours saved
- Reduced downtime: ~$500-1000/hour saved

## Documentation & Training

### Required Documentation

1. **Backup Procedures Manual**
   - How to run manual backups
   - Backup schedule documentation
   - Troubleshooting guide

2. **Restore Procedures Manual**
   - Step-by-step restore instructions
   - Emergency contact list
   - Disaster recovery runbook

3. **MinIO Administration Guide**
   - User management
   - Bucket policies
   - Performance tuning

### Team Training

1. **Administrators**
   - MinIO console usage
   - Backup script execution
   - Restore procedures

2. **Developers**
   - Django storage API
   - File upload best practices
   - Testing with MinIO

3. **Support Staff**
   - Monitoring dashboards
   - Alert response procedures
   - Escalation paths

## Next Steps After Implementation

1. **Monitor for 1 week**
   - Watch backup success rates
   - Track storage growth
   - Identify any issues

2. **Perform restore test**
   - Test database restore
   - Test file restore
   - Document any problems

3. **Optimize**
   - Tune backup schedules
   - Adjust retention policies
   - Optimize storage costs

4. **Document lessons learned**
   - Update procedures
   - Train additional staff
   - Plan for scaling

## Success Criteria

✅ MinIO service running and accessible  
✅ All files stored in object storage  
✅ Automated daily backups running  
✅ Successful restore test completed  
✅ Backup verification passing  
✅ Team trained on procedures  
✅ Documentation complete  
✅ Monitoring and alerts configured  
✅ Disaster recovery plan tested  
✅ Zero data loss in 30 days  

## Estimated Effort

**Time**: 1.5 weeks

**Breakdown**:
- MinIO setup and configuration: 1 day
- Django storage integration: 2 days
- Backup scripts development: 2 days
- Restore procedures: 1 day
- Testing: 2 days
- Documentation: 1 day
- Training: 0.5 days

## Dependencies

**Must be completed first**:
- Step 06: Report Generation (for PDF storage)
- Current infrastructure must be operational

**Enables these steps**:
- Step 15: Advanced Analytics (requires stable storage)
- Step 16: Multi-tenant Support (requires scalable storage)

## References

- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)
- [django-storages Documentation](https://django-storages.readthedocs.io/)
- [PostgreSQL Backup Best Practices](https://www.postgresql.org/docs/current/backup.html)
- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html)

---

**Note**: This step should be implemented before going to production to ensure data safety and disaster recovery capability.

