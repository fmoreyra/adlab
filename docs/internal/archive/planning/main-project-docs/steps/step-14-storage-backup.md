# Step 14: Object Storage (Garage) & Backup/Restore System

## Scope — For Future Reference

**Implement now (current task):**
- Get **Garage** up and running (Docker, config, layout, buckets, keys).
- **Django talking to Garage**: django-storages S3 backend, settings, models and views using Garage for media (signatures, reports, microscopy images, labels).
- Verification that the app reads/writes files to Garage.

**Implement later (not in scope now):**
- Backup system (database backups, file backups, backup scripts, cron, verification).
- Restore procedures and disaster recovery.
- All content in this document about backups, restore scripts, and backup automation is **for future reference** when you implement backups in a later phase.

---

## Problem Statement

Currently, the laboratory system stores files (PDF reports, signature images, microscopy photos) directly on the application server's filesystem. This approach has several limitations:

1. **Scalability Issues**: Difficult to scale horizontally with multiple application instances
2. **Single Point of Failure**: All files lost if server fails without proper backup
3. **Backup Complexity**: Requires file-level backups alongside database backups
4. **No Versioning**: Previous versions of files are lost when updated
5. **Limited Access Control**: Basic filesystem permissions insufficient for fine-grained control
6. **No Disaster Recovery**: Missing automated backup and restore procedures
7. **Migration Difficulty**: Hard to move between environments or cloud providers

**Solution**: Implement **Garage** (lightweight, S3-compatible object storage) for centralized file management and comprehensive backup/restore strategies. Garage is designed for self-hosting on modest hardware, supports replication, and exposes a standard S3 API.

## Requirements

### Functional Requirements (RF14)

**Storage Requirements:**
- **RF14.1**: Store all application files in object storage (Garage/S3-compatible)
  - Histopathologist signature images
  - Generated PDF reports
  - Microscopy images
  - QR code labels
- **RF14.2**: Maintain file versioning for audit trail
- **RF14.3**: Generate presigned URLs for secure file access
- **RF14.4**: Support both self-hosted (Garage) and cloud (AWS S3) storage backends

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
                    │  Garage / AWS S3  │
                    │  (Object Storage)         │
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
          │  Garage          │        │  PostgreSQL      │
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

### Decisions

**Decided:**
- **Static files and assets** remain served by WhiteNoise (CSS, JS, collected static). Only **media files** (signatures, report PDFs, and any other user-generated or app-generated content) use Garage/S3.
- **File access: Django as proxy.** Garage stays internal (private bucket, not exposed to the internet). Django checks permissions and streams files from Garage to the browser. The browser never talks to Garage directly. This ensures full access control on every download and is appropriate for the sensitive medical/legal documents stored (reports, signatures). Presigned URLs are not used.

**Not yet decided (to be decided at implementation time):**

1. **Report PDF:** Save PDF on finalize and serve from storage (as in step) vs keep generating on demand and optionally store a copy in Garage.
2. **Work order PDFs:** Include WorkOrder PDF storage in this phase or leave for later when work order PDF generation is fully wired.
3. **Microscopy images and QR labels:** Wire ReportImage / label PDFs to Garage in this phase, or only signatures + report PDFs for now.
4. **Django storage config:** Use `STORAGES["default"]` (Django 4.2+) vs legacy `DEFAULT_FILE_STORAGE` + `MEDIA_ROOT`/`MEDIA_URL`; recommend using existing `STORAGES` for consistency.
5. **Signature models:** Use the same Garage-backed storage for both Histopathologist and LaboratoryStaff `signature_image` when S3 is enabled.
6. **Garage Docker image tag:** Use a specific tag (e.g. `v1.0.0`) or `latest`; verify tag exists on Docker Hub.
7. **Compose profiles:** Run Garage via `docker compose --profile garage --profile web ...` (multiple profiles) vs including Garage in the default run (e.g. no profile so a single `docker compose up` brings up app + Garage).

---

### Implementation checklist (current scope)

When implementing Garage + Django storage, do the following in order:

1. **Phase 1:** Add Garage service (config, Docker, layout, buckets, keys).
2. **Settings:** Add storage config and `MEDIA_*`; use `STORAGES["default"]` (or `DEFAULT_FILE_STORAGE`) for S3 when `USE_S3_STORAGE=true`. Ensure **tests** override default storage to `FileSystemStorage` (temp dir) so tests don’t require Garage — see [Testing (storage)](#testing-storage) below.
3. **Application code:** Use only the storage API (`storage.save()`, `storage.open()`, `.name`, `.exists()`). Never use `.path` or filesystem paths for stored files so the same code works with S3 and with FileSystemStorage in tests.
4. **PDF service:** Load signature images via storage (e.g. `storage.open(file.name, 'rb')`), not `signer.signature_image.path`.
5. **Report flow:** On finalize, generate PDF, save via storage, set `report.pdf_path` and `report.pdf_hash`. In the PDF view, serve from storage using `report.pdf_path`.
6. **Optional:** Add S3-related variables to `.env.example` for reference (see Phase 1 env section).

---

### Phase 1: Add Garage Service

Object storage is provided by **Garage** ([quick-start](https://garagehq.deuxfleurs.fr/documentation/quick-start/)).

#### 1.1 Create Garage Configuration

Create `etc/garage.toml` (or mount path of your choice):

```toml
metadata_dir = "/var/lib/garage/meta"
data_dir = "/var/lib/garage/data"

replication_mode = "none"

rpc_bind_addr = "[::]:3901"
rpc_public_addr = "127.0.0.1:3901"
rpc_secret = "CHANGE_ME_GENERATE_WITH_openssl_rand_hex_32"

bootstrap_peers = []

[s3_api]
s3_region = "garage"
api_bind_addr = "[::]:3900"
root_domain = ".s3.garage"

[s3_web]
bind_addr = "[::]:3902"
root_domain = ".web.garage"
index = "index.html"
```

Generate a secure `rpc_secret`: `openssl rand -hex 32`. For production, use persistent paths for `metadata_dir` and `data_dir` (not `/tmp`).

#### 1.2 Update Docker Compose

Add to `compose.yaml`:

```yaml
services:
  # ... existing services ...

  garage:
    image: "dxflrs/garage:v1.0"
    profiles: ["garage"]
    command: server
    volumes:
      - "./etc/garage.toml:/etc/garage.toml"
      - "garage_meta:/var/lib/garage/meta"
      - "garage_data:/var/lib/garage/data"
    ports:
      - "${GARAGE_API_PORT:-127.0.0.1:3900}:3900"
      - "3901:3901"
      - "3902:3902"
    environment:
      RUST_LOG: "garage=info"
    healthcheck:
      test: ["CMD", "garage", "status"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: "${DOCKER_RESTART_POLICY:-unless-stopped}"
    networks:
      - default

volumes:
  garage_meta:
  garage_data:
```

#### 1.3 Initialize Garage (Single-Node)

After starting the container once, create layout and buckets:

```bash
# Start Garage
docker compose --profile garage up -d garage
sleep 5

# Get node ID (first column of garage status)
docker compose exec garage garage status

# Assign layout (single node, zone dc1, capacity 1)
docker compose exec garage garage layout assign -z dc1 -c 1 <NODE_ID>
docker compose exec garage garage layout apply

# Create buckets
docker compose exec garage garage bucket create adlab-media
docker compose exec garage garage bucket create adlab-backups
docker compose exec garage garage bucket create adlab-logs

# Create API key for application
docker compose exec garage garage key new --name adlab-app-key
# Save the Key ID and Secret key from output (e.g. GK..., secret hex string)

# Allow key to read/write buckets
docker compose exec garage garage bucket allow --read --write adlab-media --key adlab-app-key
docker compose exec garage garage bucket allow --read --write adlab-backups --key adlab-app-key
docker compose exec garage garage bucket allow --read --write adlab-logs --key adlab-app-key
```

#### 1.4 Environment Configuration

Add to `.env`:

```bash
# Garage Configuration (when using Garage)
GARAGE_API_PORT=127.0.0.1:3900

# Storage Backend Selection
USE_S3_STORAGE=true

# S3-compatible (Garage): use endpoint + path-style + region "garage"
AWS_ACCESS_KEY_ID=GKxxxx
AWS_SECRET_ACCESS_KEY=<secret_from_garage_key_new>
AWS_STORAGE_BUCKET_NAME=adlab-media
AWS_S3_ENDPOINT_URL=http://garage:3900
AWS_S3_REGION_NAME=garage
AWS_S3_ADDRESSING_STYLE=path

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_S3_BUCKET=adlab-backups
BACKUP_SCHEDULE_DATABASE="0 2 * * *"
BACKUP_SCHEDULE_FILES="0 3 * * *"
BACKUP_SCHEDULE_COMPLETE="0 4 * * 0"
```

**Important for Garage**: Clients must use **path-style** bucket addressing (not virtual-hosted style) and region **`garage`**. django-storages with boto3 supports this via `AWS_S3_ENDPOINT_URL` and `AWS_S3_ADDRESSING_STYLE=path`.

#### 1.5 Garage Init Script (Optional)

Create `bin/garage-init` to create buckets (run after layout is applied):

```bash
#!/bin/bash
# Ensure Garage buckets exist. Key creation done separately via garage key new / bucket allow.

set -euo pipefail

GARAGE_CMD="${GARAGE_CMD:-docker compose exec -T garage garage}"

$GARAGE_CMD bucket create adlab-media || true
$GARAGE_CMD bucket create adlab-backups || true
$GARAGE_CMD bucket create adlab-logs || true

echo "To create app key: garage key new --name adlab-app-key"
echo "Then: garage bucket allow --read --write adlab-media --key adlab-app-key"
```

Make executable: `chmod +x bin/garage-init`.

#### 1.6 Configure mc for Backups (only when implementing backups later)

For backup scripts that use `mc`, configure an alias (e.g. on the host or in a backup container). Skip this until you implement backups.

```bash
export MC_REGION=garage
mc alias set adlab http://garage:3900 <ACCESS_KEY> <SECRET_KEY> --api S3v4
```

Replace `<ACCESS_KEY>` and `<SECRET_KEY>` with the Garage key ID and secret from `garage key new`. Use the same endpoint (e.g. `http://127.0.0.1:3900` from host) as needed.

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
    # Garage / AWS S3 Configuration
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "adlab-media")
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")  # e.g. http://garage:3900
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "us-east-1")  # Use "garage" for Garage
    # Garage requires path-style addressing (not virtual-hosted)
    AWS_S3_ADDRESSING_STYLE = os.getenv("AWS_S3_ADDRESSING_STYLE", "auto")  # "path" for Garage
    
    # S3 Configuration
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',  # 1 day cache
    }
    AWS_DEFAULT_ACL = None  # Use bucket policy
    AWS_QUERYSTRING_AUTH = True  # Use presigned URLs
    AWS_QUERYSTRING_EXPIRE = 3600  # URLs expire in 1 hour
    AWS_S3_FILE_OVERWRITE = False  # Prevent overwriting
    AWS_S3_VERIFY = True  # Verify SSL certificates
    AWS_S3_USE_SSL = True  # Use HTTPS (set False for local Garage without SSL)
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

**Current scope ends here.** With Phase 1 (Garage) and Phase 2 (Django integration) done, Garage is up and Django is talking to it. The rest of this step is for future implementation.

### Testing (storage) {#testing-storage}

- **Use S3 (Garage) in development and production** by setting `USE_S3_STORAGE=true` and configuring the S3 backend.
- **In tests, use FileSystemStorage** so the test suite does not depend on Garage or AWS. In your test settings (or when `TESTING` is true), set default storage to `FileSystemStorage` with a temp directory (e.g. `tmp_test_media`). Do not set `USE_S3_STORAGE=true` during tests.
- **Application code must use only the storage API** (`storage.save()`, `storage.open()`, `file.name`, `storage.exists()`). Do not use `file.path` or raw filesystem paths for stored files. Then the same tests remain valid when production uses S3.
- Optional: add a small set of integration tests that run with a real Garage or an S3 mock (e.g. moto) for extra confidence.

### Phase 3: Backup System Implementation — LATER (Future Reference)

**Not in current scope.** The sections below (Phase 3–5, backup/restore scripts, deployment backup steps, disaster recovery) are documented for when backups are implemented in a later phase. Focus now on Phase 1 (Garage) and Phase 2 (Django integration) only.

---

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

# Upload to Garage
if [ "${USE_S3_STORAGE:-false}" = "true" ]; then
    echo "☁️  Uploading to object storage..."
    # For Garage: ensure mc alias uses --api S3v4 and MC_REGION=garage
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
# Backup files from Garage to local storage or remote

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups/files}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BUCKET="adlab-media"
SNAPSHOT_DIR="${BACKUP_DIR}/snapshots/${TIMESTAMP}"

mkdir -p "$SNAPSHOT_DIR"

echo "📁 Starting file backup from Garage..."
echo "   Source: adlab/${BUCKET}"
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

# 2. Backup files from Garage
echo "📁 [2/5] Backing up files from Garage..."
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
  "garage_bucket": "adlab-media",
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

# Upload to Garage
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
    echo "  Remote (Garage):"
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
    # Try to fetch from Garage
    if [[ "$BACKUP_FILE" == adlab/* ]]; then
        echo "📥 Downloading from Garage..."
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
# Restore files to Garage

set -euo pipefail

function show_usage() {
    echo "Usage: $0 <backup_archive.tar.gz|directory> [--force]"
    echo ""
    echo "Available backups:"
    echo "  Local:"
    find /backups/files -name "*.tar.gz" -type f -printf "    %TY-%Tm-%Td  %p\n" | sort -r | head -10
    echo ""
    echo "  Remote (Garage):"
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
    echo "⚠️  WARNING: This will OVERWRITE files in Garage!"
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

# Upload files to Garage
echo "☁️  Uploading files to Garage..."
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

# 2. Check Garage
echo "☁️  GARAGE STORAGE" | tee -a "$REPORT_FILE"
echo "-----------------------------------" | tee -a "$REPORT_FILE"

# For Garage: mc alias must use --api S3v4 and MC_REGION=garage

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

# Database backups in Garage
DB_BACKUPS=$(mc ls --recursive adlab/adlab-backups/database/ | wc -l)
echo "  Database backups: ${DB_BACKUPS}" | tee -a "$REPORT_FILE"

# File backups in Garage
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

# Garage health (alias 'adlab' configured via mc alias set)
if mc admin info adlab &>/dev/null 2>&1; then
    echo "  ✅ Garage: Healthy (admin API)" | tee -a "$REPORT_FILE"
else
    # Garage has no admin info; check bucket access instead
    if mc ls adlab/adlab-media &>/dev/null; then
        echo "  ✅ Garage: Access OK" | tee -a "$REPORT_FILE"
    else
        echo "  ❌ Garage: Not reachable" | tee -a "$REPORT_FILE"
    fi
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
chmod +x bin/garage-init
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
        """Test saving file to S3 (Garage)."""
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

- [ ] Garage service starts successfully
- [ ] Buckets are created correctly
- [ ] Django can connect to object storage
- [ ] Files upload successfully
- [ ] Files download successfully
- [ ] Presigned URLs work correctly

## Backup Testing

- [ ] Database backup runs successfully
- [ ] Database backup uploads to object storage
- [ ] File backup creates archive
- [ ] File backup uploads to object storage
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
- [ ] (Garage) mc alias uses --api S3v4 and MC_REGION=garage
```

## Production Deployment

### Deployment Instructions

**Current task:** Get Garage up and Django talking to it. The steps below focus on that. Anything about backup scripts, `mc`, or the backup service is for **later** when you implement backups.

Deploy Garage (and optionally add to an existing deployment) as follows.

#### Prerequisites

- Docker and Docker Compose installed
- Application (web, worker, postgres) already running from main `compose.yaml`
- `.env` with `POSTGRES_*`, `SECRET_KEY`, and other app settings
- (Later, for backups: `mc` or similar S3 client where backup scripts will run)

#### Deploying with Garage

**Step 1 — Create Garage configuration**

On the server:

```bash
mkdir -p etc
```

Create `etc/garage.toml` with content from [Phase 1, §1.1](#11-create-garage-configuration). Set:

- `metadata_dir` and `data_dir` to persistent paths (e.g. `/var/lib/garage/meta` and `/var/lib/garage/data`).
- `rpc_secret` to a value from: `openssl rand -hex 32`.

**Step 2 — Add Garage to Docker Compose**

Add the `garage` service and `garage_meta` / `garage_data` volumes from [Phase 1, §1.2](#12-update-docker-compose) to your `compose.yaml`. Ensure the `garage` service is on the same Docker network as `web` so the app can reach `http://garage:3900`.

**Step 3 — Start Garage and apply layout**

```bash
docker compose --profile garage up -d garage
sleep 5

# Get node ID (first column)
docker compose exec garage garage status

# Assign layout (single node; use your node ID or prefix, e.g. 563e)
docker compose exec garage garage layout assign -z dc1 -c 1 <NODE_ID>
docker compose exec garage garage layout apply
```

**Step 4 — Create buckets and application key**

```bash
docker compose exec garage garage bucket create adlab-media
docker compose exec garage garage bucket create adlab-backups
docker compose exec garage garage bucket create adlab-logs

docker compose exec garage garage key new --name adlab-app-key
# Save the Key ID (GK...) and Secret key from the output.

docker compose exec garage garage bucket allow --read --write adlab-media --key adlab-app-key
docker compose exec garage garage bucket allow --read --write adlab-backups --key adlab-app-key
docker compose exec garage garage bucket allow --read --write adlab-logs --key adlab-app-key
```

**Step 5 — Configure application environment**

In `.env` (or your production env source):

```bash
USE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=<Key ID from step 4>
AWS_SECRET_ACCESS_KEY=<Secret key from step 4>
AWS_STORAGE_BUCKET_NAME=adlab-media
AWS_S3_ENDPOINT_URL=http://garage:3900
AWS_S3_REGION_NAME=garage
AWS_S3_ADDRESSING_STYLE=path
```

**Step 6 — Restart application and verify storage**

```bash
docker compose up -d web worker
docker compose exec web python manage.py shell -c "
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
default_storage.save('deploy-test.txt', ContentFile(b'ok'))
assert default_storage.exists('deploy-test.txt')
print('Storage OK')
"
```

**Step 7 — Configure mc for backup scripts (LATER)**

When you implement backups, where backup scripts run (host or backup container), set an alias so `mc` talks to Garage:

```bash
export MC_REGION=garage
mc alias set adlab http://garage:3900 <Key_ID> <Secret_key> --api S3v4
```

Use the same Key ID and Secret as in step 5. If backups run in a container, ensure it can resolve and reach `garage:3900` (e.g. attach the container to the same Docker network and use hostname `garage`).

**Step 8 — Enable automated backups (LATER)**

When you implement the backup system:

```bash
docker compose --profile backup up -d
# Ensure the backup container has mc configured (e.g. same alias) and network access to garage.
```

---

#### Post-deployment checklist (current task: Garage + Django)

- [ ] Garage is running and reachable from the app.
- [ ] `USE_S3_STORAGE=true` and correct `AWS_*` (and for Garage: `AWS_S3_ADDRESSING_STYLE=path`, `AWS_S3_REGION_NAME=garage`) in production `.env`.
- [ ] Django can save and read a test file (step 6 above).

*(When you implement backups later: mc alias, backup scripts, backup service.)*

---

### Pre-Deployment Checklist

Quick verification before going live. For full step-by-step deployment, see [Deployment Instructions](#deployment-instructions) above. **Current task:** Garage + Django only (no backup steps yet).

```bash
# 1. Update dependencies
docker compose exec web uv sync

# 2. Run migrations
docker compose exec web python manage.py migrate

# 3. Start Garage
docker compose --profile garage up -d

# 4. Initialize (layout + buckets + key per Deployment Instructions above)

# 5. Test storage (after .env is set)
docker compose exec web python manage.py shell <<EOF
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
default_storage.save("test.txt", ContentFile(b"test"))
assert default_storage.exists("test.txt")
print("✅ Storage working!")
EOF

# 6. Ensure USE_S3_STORAGE=true in production .env

# 7. Restart application
docker compose restart web worker
```

*(When you implement backups later: run backup scripts, verify-backups, backup service.)*

### Monitoring & Alerts

Set up monitoring for:

1. **Backup Success/Failure**
   - Monitor backup logs
   - Alert on failed backups
   - Track backup duration

2. **Storage Health**
   - Monitor Garage uptime
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

**Garage (Self-Hosted)**:
- Server: $0 (uses existing infrastructure)
- Disk (500GB): ~$20-40 per month
- Lightweight: 512MB–1GB RAM per node
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

3. **Garage Administration Guide**
   - Layout, buckets, keys, `garage bucket allow`
   - Performance tuning

### Team Training

1. **Administrators**
   - Garage CLI (`garage status`, bucket/key management)
   - Backup script execution
   - Restore procedures

2. **Developers**
   - Django storage API
   - File upload best practices
   - Testing with Garage

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

**Current scope (Garage + Django):**
- ✅ Garage service running and accessible
- ✅ Django reads and writes files to Garage (media: signatures, reports, etc.)
- ✅ `USE_S3_STORAGE=true` and correct env in production
- ✅ Storage test passes (save/read file via default_storage)

**Later (when backups are implemented):**
- ✅ Automated daily backups running
- ✅ Successful restore test completed
- ✅ Backup verification passing
- ✅ Team trained on procedures
- ✅ Disaster recovery plan tested  

## Estimated Effort

**Time**: 1.5 weeks

**Breakdown**:
- Garage setup and configuration: 1 day
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

- [Garage Quick Start](https://garagehq.deuxfleurs.fr/documentation/quick-start/)
- [Garage S3 API & Client Configuration](https://garagehq.deuxfleurs.fr/cookbook/clients.html)
- [django-storages Documentation](https://django-storages.readthedocs.io/)
- [PostgreSQL Backup Best Practices](https://www.postgresql.org/docs/current/backup.html)
- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html)

---

**Note**: This step should be implemented before going to production to ensure data safety. **Current focus:** Garage + Django storage integration only. Backup/restore is for a later phase.

