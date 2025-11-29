#!/usr/bin/env bash

# CI test pipeline script
# Extracted from the original run script

set -o errexit
set -o pipefail

# Source docker helper functions
# shellcheck source=scripts/docker-helper.sh
source "$(dirname "$0")/docker-helper.sh"

# Lint Dockerfile
lint_dockerfile() {
  docker container run --rm -i \
    -v "${PWD}/.hadolint.yaml:/.config/hadolint.yaml" \
    hadolint/hadolint hadolint "${@}" - <Dockerfile
}

# Lint shell scripts
lint_shell() {
  local cmd=(shellcheck)

  if ! command -v shellcheck >/dev/null 2>&1; then
    local cmd=(docker container run --rm -i -v "${PWD}:/mnt" koalaman/shellcheck:stable)
  fi

  find . -type f \
    ! -path "./.git/*" \
    ! -path "./.ruff_cache/*" \
    ! -path "./.pytest_cache/*" \
    ! -path "./assets/*" \
    ! -path "./public/*" \
    ! -path "./public_collected/*" \
    ! -name "*.md" \
    -exec grep --quiet '^#!.*sh' {} \; -exec "${cmd[@]}" {} +
}

# Format shell scripts (check only)
format_shell_check() {
  local cmd=(shfmt)

  if ! command -v shfmt >/dev/null 2>&1; then
    local cmd=(docker container run --rm -i -v "${PWD}:/mnt" -u "$(id -u):$(id -g)" -w /mnt mvdan/shfmt:v3)
  fi

  # Find shell scripts excluding .md files and other non-script directories
  # Only process files that have a shell shebang to avoid processing .md files
  local files
  files=$(find . -type f \
    ! -path "./.git/*" \
    ! -path "./.ruff_cache/*" \
    ! -path "./.pytest_cache/*" \
    ! -path "./assets/*" \
    ! -path "./public/*" \
    ! -path "./public_collected/*" \
    ! -name "*.md" \
    -exec grep --quiet '^#!.*sh' {} \; -print)

  if [ -n "$files" ]; then
    echo "$files" | xargs "${cmd[@]}" --diff
  else
    echo "No shell scripts found to format."
  fi
}

# Create wait-until function if not available
create_wait_until() {
  if ! command -v wait-until >/dev/null 2>&1; then
    echo "Creating wait-until function..."
    # shellcheck disable=SC2178
    wait-until() {
      # shellcheck disable=SC2128
      local cmd="$*"
      local max_attempts=30
      local attempt=1

      while [ $attempt -le $max_attempts ]; do
        # shellcheck disable=SC2128
        if eval "$cmd" >/dev/null 2>&1; then
          return 0
        fi
        echo "Attempt $attempt/$max_attempts: waiting for command to succeed..."
        sleep 2
        attempt=$((attempt + 1))
      done

      # shellcheck disable=SC2128
      echo "Command failed after $max_attempts attempts: $cmd"
      return 1
    }
  fi
}

# Main CI test execution
main() {
  echo "🚀 Starting CI test pipeline..."

  # Run linting
  lint_dockerfile "${@}"
  lint_shell
  format_shell_check

  # Copy .env.example to .env if .env doesn't exist
  if [ ! -f .env ]; then
    cp .env.example .env
  fi

  # Build and start containers
  docker compose build
  docker compose up -d

  # Load environment variables
  # shellcheck disable=SC1091
  . .env

  # Create wait-until function
  create_wait_until

  # Wait for database to be ready
  wait-until "docker compose exec -T \
    -e PGPASSWORD=${POSTGRES_PASSWORD} postgres \
    psql -U ${POSTGRES_USER} ${POSTGRES_DB} -c 'SELECT 1'"

  # Show logs
  docker compose logs

  # Run Python linting
  _dc web ruff check "${@}"

  # Check Python formatting
  _dc web ruff format --check --diff

  # Run migrations
  _dc web python3 manage.py migrate

  # Run tests
  RUNNING_TESTS=true _dc -e DJANGO_TESTING=true -e RUNNING_TESTS=true web python3 manage.py test

  echo "✅ CI test pipeline completed successfully!"
}

main "$@"
