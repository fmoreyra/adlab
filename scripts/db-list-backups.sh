#!/usr/bin/env bash

# Database backup listing script
# Extracted from the original run script

set -o errexit
set -o pipefail

main() {
  local backup_dir="./backups"

  if [ ! -d "${backup_dir}" ]; then
    echo "📁 No backup directory found at ${backup_dir}"
    return 0
  fi

  local backup_count
  backup_count=$(find "${backup_dir}" -name "adlab_dump_*.sql" | wc -l)

  if [ "${backup_count}" -eq 0 ]; then
    echo "📁 No database backups found in ${backup_dir}"
    return 0
  fi

  echo "🗄️  Available database backups:"
  echo "📁 Directory: ${backup_dir}"
  echo ""

  # List backups with file size and date
  find "${backup_dir}" -name "adlab_dump_*.sql" -type f -exec ls -lh {} \; |
    awk '{print "📄 " $9 " (" $5 ", " $6 " " $7 " " $8 ")"}' |
    sort -r
}

main "$@"
