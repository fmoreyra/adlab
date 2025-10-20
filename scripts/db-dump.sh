#!/usr/bin/env bash

# Database dump script
# Extracted from the original run script

set -o errexit
set -o pipefail

# Source docker helper functions
# shellcheck source=scripts/docker-helper.sh
source "$(dirname "$0")/docker-helper.sh"

main() {
  local timestamp
  timestamp=$(date +"%Y%m%d_%H%M%S")
  local backup_dir="./backups"
  local dump_file="${backup_dir}/adlab_dump_${timestamp}.sql"

  # Create backup directory if it doesn't exist
  mkdir -p "${backup_dir}"

  echo "🗄️  Generating database dump..."
  echo "📁 Backup directory: ${backup_dir}"
  echo "📄 Dump file: $(basename "${dump_file}")"
  echo ""

  # Load environment variables
  # shellcheck disable=SC1091
  . .env

  # Generate the dump using pg_dump
  _dc postgres pg_dump \
    -U "${POSTGRES_USER}" \
    -h localhost \
    -p 5432 \
    "${POSTGRES_DB}" \
    --no-password \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --format=plain \
    --file="/tmp/dump_${timestamp}.sql"

  # Copy the dump file from the container to the host
  docker compose cp "postgres:/tmp/dump_${timestamp}.sql" "${dump_file}"

  # Clean up the temporary file in the container
  _dc postgres rm -f "/tmp/dump_${timestamp}.sql"

  if [ -f "${dump_file}" ]; then
    local file_size
    file_size=$(du -h "${dump_file}" | cut -f1)
    echo ""
    echo "✅ Database dump created successfully!"
    echo "📊 File size: ${file_size}"
    echo "📍 Location: ${dump_file}"
  else
    echo ""
    echo "❌ Failed to create database dump"
    return 1
  fi
}

main "$@"
