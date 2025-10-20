#!/usr/bin/env bash

# Database restore script
# Extracted from the original run script

set -o errexit
set -o pipefail

# Source docker helper functions
# shellcheck source=scripts/docker-helper.sh
source "$(dirname "$0")/docker-helper.sh"

main() {
  local dump_file="${1:-}"

  if [ -z "${dump_file}" ]; then
    echo "❌ Please provide a dump file path"
    echo "Usage: $0 <path_to_dump_file>"
    return 1
  fi

  if [ ! -f "${dump_file}" ]; then
    echo "❌ Dump file not found: ${dump_file}"
    return 1
  fi

  echo "🗄️  Restoring database from dump..."
  echo "📄 Dump file: ${dump_file}"
  echo ""

  # Load environment variables
  # shellcheck disable=SC1091
  . .env

  # Copy the dump file to the container
  local temp_dump
  temp_dump="/tmp/restore_$(basename "${dump_file}")"
  docker compose cp "${dump_file}" "postgres:${temp_dump}"

  # Restore the database
  _dc postgres psql \
    -U "${POSTGRES_USER}" \
    -h localhost \
    -p 5432 \
    -d postgres \
    --no-password \
    -f "${temp_dump}"

  # Clean up the temporary file in the container
  _dc postgres rm -f "${temp_dump}"

  echo ""
  echo "✅ Database restored successfully!"
}

main "$@"
