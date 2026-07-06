#!/usr/bin/env bash
#
# Restore a complete backup created by backup-complete.sh.
#
# Usage:
#   ./bin/restore-complete.sh backups/adlab_complete_YYYYMMDD_HHMMSS
#   ./bin/restore-complete.sh backups/adlab_complete_YYYYMMDD_HHMMSS --force
#
set -o errexit
set -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/docker-helper.sh
source "${ROOT}/scripts/docker-helper.sh"

FORCE=false

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

usage() {
  echo "Usage: $0 <backup-directory> [--force]"
  echo ""
  echo "Example:"
  echo "  $0 backups/adlab_complete_20260704_172342"
  exit 1
}

parse_args() {
  if [[ $# -lt 1 ]]; then
    usage
  fi

  BACKUP_DIR="$1"
  shift

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --force | -f)
        FORCE=true
        ;;
      -h | --help)
        usage
        ;;
      *)
        fail "Unknown argument: $1"
        ;;
    esac
    shift
  done

  if [[ ! -d "$BACKUP_DIR" ]]; then
    fail "Backup directory not found: ${BACKUP_DIR}"
  fi

  BACKUP_DIR="$(cd "$BACKUP_DIR" && pwd)"

  if [[ ! -f "${BACKUP_DIR}/database.sql.gz" ]]; then
    fail "Missing ${BACKUP_DIR}/database.sql.gz"
  fi

  if [[ ! -f "${BACKUP_DIR}/manifest.json" ]]; then
    log "Warning: manifest.json not found — proceeding anyway."
  fi
}

confirm_restore() {
  if [[ "$FORCE" == true ]]; then
    return 0
  fi

  # shellcheck disable=SC1091
  source .env

  echo ""
  echo "This will REPLACE the current database (${POSTGRES_DB}) and media files."
  echo "Backup source: ${BACKUP_DIR}"
  read -r -p "Continue? [y/N] " reply
  if [[ ! "$reply" =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 0
  fi
}

check_prerequisites() {
  if [[ ! -f ".env" ]]; then
    fail ".env not found"
  fi
  if ! docker info >/dev/null 2>&1; then
    fail "Docker is not running"
  fi
  if ! docker compose ps postgres --status running -q 2>/dev/null | grep -q .; then
    fail "postgres service is not running"
  fi
}

stop_app_services() {
  log_step "Stopping web, worker, and beat"
  docker compose stop web worker beat 2>/dev/null || true
}

restore_database() {
  log_step "Restoring database from ${BACKUP_DIR}/database.sql.gz"

  # shellcheck disable=SC1091
  source .env

  gunzip -c "${BACKUP_DIR}/database.sql.gz" \
    | docker compose exec -T postgres psql \
      -U "${POSTGRES_USER}" \
      -h localhost \
      -p 5432 \
      -d postgres \
      --no-password \
      -v ON_ERROR_STOP=1 \
      -q \
      2>/dev/null

  log "Database restore OK"
}

restore_media() {
  if [[ ! -d "${BACKUP_DIR}/media" ]] || [[ -z "$(ls -A "${BACKUP_DIR}/media" 2>/dev/null)" ]]; then
    log "No media in backup — skipping media restore."
    return 0
  fi

  log_step "Restoring media files"

  mkdir -p "${ROOT}/media"
  cp -a "${BACKUP_DIR}/media/." "${ROOT}/media/"
  log "Copied media to host ./media/"

  if docker compose ps web -q 2>/dev/null | grep -q .; then
    docker compose exec -T web mkdir -p /app/media 2>/dev/null || true
    docker compose cp "${BACKUP_DIR}/media/." "web:/app/media/"
    log "Copied media to web:/app/media/"
  else
    log "Web container not found — media only on host ./media/"
  fi
}

start_app_services() {
  log_step "Starting web, worker, and beat"
  # Use start (not up -d) to avoid image rebuilds during restore.
  for svc in web worker beat; do
    if docker compose ps -a --services 2>/dev/null | grep -qx "$svc"; then
      docker compose start "$svc" || true
    fi
  done
}

main() {
  parse_args "$@"
  check_prerequisites
  confirm_restore
  stop_app_services
  restore_database
  restore_media
  start_app_services

  log_step "Restore complete"
  if [[ -f "${BACKUP_DIR}/manifest.json" ]]; then
    log "Restored from manifest:"
    cat "${BACKUP_DIR}/manifest.json"
  fi
}

main "$@"
