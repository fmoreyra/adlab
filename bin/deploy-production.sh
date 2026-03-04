#!/usr/bin/env bash

# Production Deployment Script for Laboratory System
# This script deploys using production compose files with Nginx

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

COMPOSE_FILES="-f compose.yaml -f compose.production.yaml"

# So make manage / docker compose use the same project when we exec into web
export COMPOSE_FILE=compose.yaml:compose.production.yaml

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${PURPLE}🔄 $1${NC}"; }

# Check if we're in production mode
check_production_mode() {
  if [[ ! -f ".env" ]]; then
    log_error ".env file not found"
    exit 1
  fi

  # shellcheck disable=SC1091
  source .env

  local debug_val
  debug_val="$(echo "${DEBUG:-true}" | tr '[:upper:]' '[:lower:]')"
  if [[ "$debug_val" == "true" ]]; then
    log_error "DEBUG is set to True. This is not safe for production!"
    log_error "Set DEBUG=False in .env file"
    exit 1
  fi

  if [[ -z "${ALLOWED_HOSTS:-}" ]]; then
    log_error "ALLOWED_HOSTS is not set in .env"
    exit 1
  fi

  log_success "Production mode verified"
}

# Backup database
backup_database() {
  log_step "Creating database backup..."

  if make db-dump; then
    log_success "Database backup completed (see ./backups directory)"
  else
    log_error "Database backup failed"
    exit 1
  fi
}

start_infrastructure() {
  log_step "Starting core services (postgres, redis)..."

  # shellcheck disable=SC2086
  docker compose $COMPOSE_FILES up -d postgres redis
}

start_garage() {
  log_step "Starting object storage (Garage)..."

  # shellcheck disable=SC2086
  docker compose $COMPOSE_FILES up -d garage

  local max_attempts=15
  local attempt=1
  while [[ $attempt -le $max_attempts ]]; do
    # shellcheck disable=SC2086
    if docker compose $COMPOSE_FILES exec -T garage /garage status >/dev/null 2>&1; then
      log_success "Garage is healthy"

      # First-time init: if bucket doesn't exist yet, run garage-init
      # shellcheck disable=SC2086
      if ! docker compose $COMPOSE_FILES exec -T garage /garage bucket info "${AWS_STORAGE_BUCKET_NAME:-adlab-media}" >/dev/null 2>&1; then
        log_info "Running first-time Garage initialization..."
        bin/garage-init
      fi
      return 0
    fi
    log_info "Waiting for Garage... ($attempt/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
  done

  log_error "Garage failed health check after $((max_attempts * 2)) seconds"
  exit 1
}

start_app_services() {
  log_step "Starting application services (web, worker, beat)..."

  # shellcheck disable=SC2086
  docker compose $COMPOSE_FILES up -d web worker beat
}

start_proxy() {
  log_step "Starting reverse proxy (nginx) and SSL renewal (certbot)..."

  # Force-recreate so Nginx re-resolves the upstream DNS (web container IP may
  # have changed after restart_services force-recreated it).
  # shellcheck disable=SC2086
  docker compose $COMPOSE_FILES up -d --force-recreate nginx

  # Start the certbot container which renews certificates every 12h.
  # Nginx reloads every 6h to pick up renewed certs (see compose.production.yaml).
  # shellcheck disable=SC2086
  docker compose $COMPOSE_FILES up -d certbot
}

# Pull latest changes
pull_changes() {
  log_step "Pulling latest changes..."

  git fetch origin
  local current
  current=$(git rev-parse HEAD)
  local remote
  remote=$(git rev-parse origin/main)

  if [[ "$current" == "$remote" ]]; then
    log_info "Already up to date"
    return 0
  fi

  git pull origin main
  log_success "Updated to latest version"
}

# Build images
build_images() {
  log_step "Building Docker images..."
  # shellcheck disable=SC2086
  docker compose $COMPOSE_FILES build
  log_success "Images built successfully"
}

# Build documentation
build_documentation() {
  log_step "Building documentation..."

  if make docs-build; then
    log_success "Documentation built successfully"
  else
    log_warning "Documentation build failed; continuing deployment"
    log_info "Run 'make docs-build' manually to inspect the error"
  fi
}

# Run migrations
run_migrations() {
  log_step "Running migrations..."

  if ! make manage ARGS="migrate --check"; then
    log_error "Migration check failed"
    exit 1
  fi

  make manage ARGS="migrate --no-input"
  log_success "Migrations applied"
}

# Collect static files
collect_static() {
  log_step "Collecting static files..."

  # Ensure app images exist in repo so the image build (and collectstatic) can include them.
  if [[ ! -f "assets/static/images/logo-unl-fcv.png" ]]; then
    log_error "assets/static/images/logo-unl-fcv.png is missing from the repo."
    log_error "Add the file and redeploy. If it was removed, restore it from git."
    exit 1
  fi

  # Rebuild manifest and collected files from the image's static sources (repair
  # references like images/logo-unl-fcv.png). The web container was started from
  # the image we just built, so /public in the container includes app images from
  # assets/static/images/. Ensure those files are committed so the image build has them.
  make manage ARGS="collectstatic --no-input --clear"
  log_success "Static files collected successfully"
}

# Restart app services (web, worker, beat)
restart_services() {
  log_step "Restarting application services..."

  # Force-recreate app services so that Gunicorn/WhiteNoise re-reads the
  # freshly generated staticfiles.json manifest.  A plain "up -d" skips
  # containers whose image + config haven't changed, leaving the process
  # running with a stale (or empty) cached manifest from before
  # collect_static ran.
  # shellcheck disable=SC2086
  docker compose $COMPOSE_FILES up -d --force-recreate web worker beat

  log_success "Application services restarted"
}

# Verify all services are healthy (must run after nginx is up)
verify_health() {
  log_step "Verifying services are healthy..."

  local max_attempts=30
  local attempt=1

  while [[ $attempt -le $max_attempts ]]; do
    if curl -sf http://localhost/up >/dev/null 2>&1; then
      log_success "Services are healthy"
      return 0
    fi
    log_info "Waiting for services... ($attempt/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
  done

  log_error "Services failed health check after $((max_attempts * 2)) seconds"
  exit 1
}

# Main deployment
main() {
  echo -e "${PURPLE}🚀 Starting production deployment${NC}"
  echo -e "${PURPLE}=================================${NC}"
  echo

  check_production_mode
  start_infrastructure
  start_garage
  backup_database
  pull_changes
  build_images
  start_app_services
  run_migrations
  collect_static
  build_documentation
  restart_services
  start_proxy
  verify_health

  echo
  echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
  echo -e "${GREEN}Check your site at: https://\$DOMAIN_NAME${NC}"
  echo -e "${GREEN}Documentation at: https://\$DOMAIN_NAME/static/docs/${NC}"
  echo
}

trap 'log_error "Deployment interrupted"; exit 1' INT TERM
main "$@"
