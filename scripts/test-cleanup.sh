#!/usr/bin/env bash

# Test database cleanup script
# Extracted from the original run script

set -o errexit
set -o pipefail

main() {
  echo "🧹 Cleaning up test database..."
  # Terminate any lingering connections to test database
  echo "1. Terminating connections to test database..."
  docker compose exec postgres psql -U adlab -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'test_adlab' AND pid <> pg_backend_pid();" 2>/dev/null || true
  # Wait a moment for connections to close
  sleep 2
  # Drop the test database
  echo "2. Dropping test database..."
  docker compose exec postgres psql -U adlab -d postgres -c "DROP DATABASE IF EXISTS test_adlab;" 2>/dev/null || true
  echo "✅ Test database cleanup completed"
}

main "$@"
