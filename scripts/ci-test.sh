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

  # Activate necessary profiles for all docker compose commands
  # postgres, redis, web, worker are required for CI tests
  export COMPOSE_PROFILES=postgres,redis,web,worker
  echo "COMPOSE_PROFILES=${COMPOSE_PROFILES}"

  # Run linting
  lint_dockerfile "${@}"
  lint_shell
  format_shell_check

  # Copy .env.example to .env if .env doesn't exist
  if [ ! -f .env ]; then
    cp .env.example .env
  fi

  # Ensure POSTGRES_DB is set in .env file (it's commented out in .env.example)
  if ! grep -q "^export POSTGRES_DB=" .env && ! grep -q "^POSTGRES_DB=" .env; then
    echo "export POSTGRES_DB=adlab" >>.env
  elif grep -q "^#export POSTGRES_DB=" .env || grep -q "^#POSTGRES_DB=" .env; then
    # Uncomment if it's commented
    sed -i 's/^#export POSTGRES_DB=.*/export POSTGRES_DB=adlab/' .env
    sed -i 's/^#POSTGRES_DB=.*/POSTGRES_DB=adlab/' .env
  fi

  # Load environment variables BEFORE starting containers
  # Docker compose needs these variables to start postgres properly
  # shellcheck disable=SC1091
  . .env

  # Set POSTGRES_DB if still not set (fallback)
  export POSTGRES_DB="${POSTGRES_DB:-adlab}"

  # Verify required postgres variables are set and export them
  if [ -z "${POSTGRES_USER:-}" ] || [ -z "${POSTGRES_PASSWORD:-}" ]; then
    echo "ERROR: Required postgres environment variables not set!"
    echo "POSTGRES_DB=${POSTGRES_DB:-NOT SET}"
    echo "POSTGRES_USER=${POSTGRES_USER:-NOT SET}"
    echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD:+SET}"
    exit 1
  fi

  # Ensure all postgres variables are exported for docker compose
  export POSTGRES_USER
  export POSTGRES_PASSWORD
  export POSTGRES_DB

  echo "Postgres configuration:"
  echo "  POSTGRES_DB=${POSTGRES_DB}"
  echo "  POSTGRES_USER=${POSTGRES_USER}"
  echo "  POSTGRES_PASSWORD=${POSTGRES_PASSWORD:+SET}"

  # Build and start containers
  echo "Building containers..."
  docker compose build
  echo "Starting containers with profiles: ${COMPOSE_PROFILES}"
  docker compose up -d

  # Give containers a moment to start
  sleep 5

  echo "Container status:"
  docker compose ps
  echo ""
  echo "All containers (including stopped):"
  docker ps -a

  # Create wait-until function
  create_wait_until

  # Check if postgres container crashed and show logs
  if docker ps -a --filter "name=postgres" --format "{{.Status}}" | grep -q "Exited"; then
    echo "ERROR: postgres container exited. Checking logs..."
    docker compose logs postgres
    echo ""
    echo "Postgres container environment variables:"
    docker inspect adlab-postgres-1 --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep POSTGRES || true
    exit 1
  fi

  # Wait for postgres service to be running (check container status)
  echo "Waiting for postgres service to start..."
  wait-until "docker compose ps postgres 2>/dev/null | grep -q 'Up' || docker ps --filter 'name=postgres' --format '{{.Status}}' | grep -q 'Up'"

  # Wait for database to be ready
  echo "Waiting for database to be ready..."
  wait-until "docker compose exec -T \
    -e PGPASSWORD=${POSTGRES_PASSWORD} postgres \
    psql -U ${POSTGRES_USER} ${POSTGRES_DB} -c 'SELECT 1' >/dev/null 2>&1"

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
