#!/usr/bin/env bash
#
# Create a complete backup: PostgreSQL dump (gzip) + media files + manifest.
#
# Output: backups/adlab_complete_YYYYMMDD_HHMMSS/
#   ├── manifest.json
#   ├── database.sql.gz
#   └── media/          (signatures, reports, etc.)
#
# Media source (auto-detected):
#   1. Host ./media/ if it exists and is non-empty
#   2. Else web container /app/media/ (typical VPS without host volume)
#   3. S3/Garage: logged as skipped until mc mirror is implemented
#
set -o errexit
set -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/docker-helper.sh
source "${ROOT}/scripts/docker-helper.sh"

log() {
  echo "$*"
}

log_step() {
  echo ""
  echo "==> $*"
}

fail() {
  echo "Error: $*" >&2
  exit 1
}

check_prerequisites() {
  if [[ ! -f ".env" ]]; then
    fail ".env not found. Copy from .env.example"
  fi
  if [[ ! -f "compose.yaml" ]]; then
    fail "compose.yaml not found. Run from project root."
  fi
  if ! docker info >/dev/null 2>&1; then
    fail "Docker is not running."
  fi
  if ! docker compose ps postgres --status running -q 2>/dev/null | grep -q .; then
    fail "postgres service is not running. Start with: docker compose up -d"
  fi
}

backup_database() {
  local dest="$1"

  log_step "Backing up database to ${dest}"

  # shellcheck disable=SC1091
  source .env

  docker compose exec -T postgres pg_dump \
    -U "${POSTGRES_USER}" \
    -h localhost \
    -p 5432 \
    "${POSTGRES_DB}" \
    --no-password \
    --clean \
    --if-exists \
    --create | gzip >"${dest}/database.sql.gz"

  if [[ ! -s "${dest}/database.sql.gz" ]]; then
    fail "database backup is empty"
  fi

  log "Database backup OK ($(du -h "${dest}/database.sql.gz" | cut -f1))"
}

backup_media() {
  local dest="$1"
  local media_dest="${dest}/media"

  log_step "Backing up media files"

  # shellcheck disable=SC1091
  source .env

  mkdir -p "${media_dest}"

  local use_s3
  use_s3="$(echo "${USE_S3_STORAGE:-false}" | tr '[:upper:]' '[:lower:]')"

  if [[ "$use_s3" == "true" ]]; then
    log "USE_S3_STORAGE=true — S3/Garage media mirror not implemented yet."
    log "Database backup will proceed; restore media manually from bucket if needed."
    return 0
  fi

  if [[ -d "${ROOT}/media" ]] && [[ -n "$(ls -A "${ROOT}/media" 2>/dev/null)" ]]; then
    log "Copying from host ./media/"
    cp -a "${ROOT}/media/." "${media_dest}/"
  elif docker compose ps web --status running -q 2>/dev/null | grep -q .; then
    log "Copying from web container (web:/app/media/)"
    if docker compose exec -T web test -d /app/media 2>/dev/null; then
      docker compose cp "web:/app/media/." "${media_dest}/"
    else
      log "No /app/media in web container — skipping media files."
    fi
  else
    log "No host ./media/ and web container not running — skipping media files."
  fi

  if [[ -n "$(ls -A "${media_dest}" 2>/dev/null)" ]]; then
    log "Media backup OK ($(du -sh "${media_dest}" | cut -f1))"
  else
    log "Media backup empty (no uploads yet)."
    rmdir "${media_dest}" 2>/dev/null || true
  fi
}

write_manifest() {
  local dest="$1"
  local timestamp="$2"

  # shellcheck disable=SC1091
  source .env

  local git_commit="unknown"
  if git rev-parse HEAD >/dev/null 2>&1; then
    git_commit="$(git rev-parse HEAD)"
  fi

  local use_s3
  use_s3="$(echo "${USE_S3_STORAGE:-false}" | tr '[:upper:]' '[:lower:]')"

  local db_bytes=0
  if [[ -f "${dest}/database.sql.gz" ]]; then
    db_bytes="$(wc -c <"${dest}/database.sql.gz" | tr -d ' ')"
  fi

  local media_bytes=0
  if [[ -d "${dest}/media" ]]; then
    media_bytes="$(du -sb "${dest}/media" 2>/dev/null | cut -f1 || echo 0)"
  fi

  cat >"${dest}/manifest.json" <<EOF
{
  "backup_type": "adlab_complete",
  "timestamp": "${timestamp}",
  "created_at_utc": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "git_commit": "${git_commit}",
  "postgres_db": "${POSTGRES_DB}",
  "postgres_user": "${POSTGRES_USER}",
  "use_s3_storage": $(if [[ "$use_s3" == "true" ]]; then echo "true"; else echo "false"; fi),
  "database_file": "database.sql.gz",
  "database_bytes": ${db_bytes},
  "media_bytes": ${media_bytes},
  "compose_project_name": "${COMPOSE_PROJECT_NAME:-}"
}
EOF

  log "Manifest written: ${dest}/manifest.json"
}

main() {
  check_prerequisites

  local timestamp
  timestamp="$(date +"%Y%m%d_%H%M%S")"
  local backup_dir="${ROOT}/backups/adlab_complete_${timestamp}"

  mkdir -p "${backup_dir}"

  log_step "Starting complete backup"
  log "Output directory: ${backup_dir}"

  backup_database "${backup_dir}"
  backup_media "${backup_dir}"
  write_manifest "${backup_dir}" "${timestamp}"

  log_step "Backup complete"
  log "Location: ${backup_dir}"
  ls -lh "${backup_dir}"
}

main "$@"
