#!/usr/bin/env bash

# Script to create an admin user on the remote server
# Usage: ./scripts/create-admin-user.sh [email] [first_name] [last_name]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# Source docker helper functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/docker-helper.sh"

# Generate secure password using Python secrets module
generate_password() {
    docker compose exec -T web python3 -c "
import secrets
import string

# Generate a secure password: 16 characters with mix of letters, digits, and symbols
alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
password = ''.join(secrets.choice(alphabet) for _ in range(16))
print(password)
"
}

# Create admin user
create_admin_user() {
    local email="${1:-admin@adlab.com}"
    local first_name="${2:-Admin}"
    local last_name="${3:-User}"
    local password
    
    log_info "Generating secure password..."
    password=$(generate_password)
    
    log_info "Creating admin user: $email"
    
    # Use Django shell to create the user
    docker compose exec -T web python3 manage.py shell <<EOF
from accounts.models import User
import secrets

email = "$email"
first_name = "$first_name"
last_name = "$last_name"
password = "$password"

# Check if user already exists
if User.objects.filter(email=email).exists():
    print(f"ERROR: User with email {email} already exists!")
    exit(1)

# Create admin user
user = User.objects.create_user(
    username=email,
    email=email,
    password=password,
    first_name=first_name,
    last_name=last_name,
    role=User.Role.ADMIN,
    is_superuser=True,
    is_staff=True,
    is_active=True,
    email_verified=True,  # Admin users don't need email verification
)

print(f"SUCCESS: Admin user created successfully!")
print(f"Email: {user.email}")
print(f"Username: {user.username}")
print(f"Role: {user.get_role_display()}")
EOF

    if [ $? -eq 0 ]; then
        echo
        log_success "Admin user created successfully!"
        echo
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}  Admin User Credentials${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${BLUE}Email:${NC}    $email"
        echo -e "${BLUE}Password:${NC}  ${YELLOW}$password${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
        echo
        log_warning "Please save this password securely. It will not be shown again."
        echo
    else
        log_error "Failed to create admin user"
        exit 1
    fi
}

# Main execution
main() {
    local email="${1:-}"
    local first_name="${2:-}"
    local last_name="${3:-}"
    
    # Check if Docker Compose is available
    if ! command -v docker compose &> /dev/null; then
        log_error "docker compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check if web service is running
    if ! docker compose ps web | grep -q "Up"; then
        log_error "Web service is not running. Please start the services first."
        exit 1
    fi
    
    # Prompt for email if not provided
    if [ -z "$email" ]; then
        read -p "Enter admin email (default: admin@adlab.com): " email
        email="${email:-admin@adlab.com}"
    fi
    
    # Prompt for first name if not provided
    if [ -z "$first_name" ]; then
        read -p "Enter first name (default: Admin): " first_name
        first_name="${first_name:-Admin}"
    fi
    
    # Prompt for last name if not provided
    if [ -z "$last_name" ]; then
        read -p "Enter last name (default: User): " last_name
        last_name="${last_name:-User}"
    fi
    
    create_admin_user "$email" "$first_name" "$last_name"
}

main "$@"


