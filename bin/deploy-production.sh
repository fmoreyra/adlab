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

PROJECT_NAME="Laboratory System"
COMPOSE_FILES="-f compose.yaml -f compose.production.yaml"

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

  source .env

  if [[ "${DEBUG:-true}" == "True" ]]; then
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
  
  local backup_dir="./backups"
  mkdir -p "$backup_dir"
  
  local timestamp=$(date +"%Y%m%d_%H%M%S")
  local backup_file="$backup_dir/db_backup_$timestamp.sql.gz"

  source .env
  docker compose $COMPOSE_FILES exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$backup_file"

  if [[ -f "$backup_file" ]] && [[ -s "$backup_file" ]]; then
    log_success "Database backed up to: $backup_file"
  else
    log_error "Database backup failed"
    exit 1
  fi
}

# Pull latest changes
pull_changes() {
  log_step "Pulling latest changes..."
  
  git fetch origin
  local current=$(git rev-parse HEAD)
  local remote=$(git rev-parse origin/main)

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
  docker compose $COMPOSE_FILES build
  log_success "Images built successfully"
}

# Run migrations
run_migrations() {
  log_step "Running migrations..."
  
  if ! ./run manage migrate --check; then
    log_error "Migration check failed"
    exit 1
  fi

  ./run manage migrate --no-input
  log_success "Migrations applied"
}

# Restart services
restart_services() {
  log_step "Restarting services..."
  
  # Restart app services (not nginx)
  docker compose $COMPOSE_FILES restart web worker beat
  
  # Wait for health check
  local max_attempts=30
  local attempt=1

  while [[ $attempt -le $max_attempts ]]; do
    if curl -sf http://localhost/up > /dev/null 2>&1; then
      log_success "Services are healthy"
      return 0
    fi
    log_info "Waiting for services... ($attempt/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
  done

  log_error "Services failed to start"
  exit 1
}

# Main deployment
main() {
  echo -e "${PURPLE}🚀 Starting production deployment${NC}"
  echo -e "${PURPLE}=================================${NC}"
  echo

  check_production_mode
  backup_database
  pull_changes
  build_images
  run_migrations
  restart_services

  echo
  echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
  echo -e "${GREEN}Check your site at: https://\$DOMAIN_NAME${NC}"
  echo
}

trap 'log_error "Deployment interrupted"; exit 1' INT TERM
main "$@"
