#!/usr/bin/env bash

# Initialize Let's Encrypt SSL certificates for production deployment
# Usage: ./bin/init-letsencrypt.sh your-domain.com admin@example.com [staging]

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DOMAIN="${1:-}"
EMAIL="${2:-}"
STAGING="${3:-0}" # Set to 1 for testing

if [[ -z "$DOMAIN" ]] || [[ -z "$EMAIL" ]]; then
  echo "Usage: $0 <domain> <email> [staging]"
  echo "Example: $0 lab.example.com admin@example.com"
  echo "Example (staging): $0 lab.example.com admin@example.com 1"
  exit 1
fi

echo -e "${BLUE}### Initializing Let's Encrypt for $DOMAIN${NC}"

# Create required directories
mkdir -p certbot/conf certbot/www nginx/conf.d

# Download recommended TLS parameters
if [ ! -e "certbot/conf/options-ssl-nginx.conf" ]; then
  echo -e "${YELLOW}### Downloading recommended TLS parameters...${NC}"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf >certbot/conf/options-ssl-nginx.conf
fi

if [ ! -e "certbot/conf/ssl-dhparams.pem" ]; then
  echo -e "${YELLOW}### Downloading recommended DH parameters...${NC}"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem >certbot/conf/ssl-dhparams.pem
fi

# Create Nginx configuration from template
echo -e "${YELLOW}### Creating Nginx configuration for $DOMAIN...${NC}"
sed "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" nginx/conf.d/laboratory.conf.template >nginx/conf.d/laboratory.conf

# Create dummy certificate for initial Nginx startup
echo -e "${YELLOW}### Creating dummy certificate for $DOMAIN...${NC}"
mkdir -p "certbot/conf/live/$DOMAIN"
docker compose -f compose.yaml -f compose.production.yaml run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout '/etc/letsencrypt/live/$DOMAIN/privkey.pem' \
    -out '/etc/letsencrypt/live/$DOMAIN/fullchain.pem' \
    -subj '/CN=localhost'" certbot

# Start Nginx
echo -e "${YELLOW}### Starting Nginx...${NC}"
docker compose -f compose.yaml -f compose.production.yaml up -d nginx

# Wait for Nginx to be ready
sleep 5

# Delete dummy certificate
echo -e "${YELLOW}### Deleting dummy certificate...${NC}"
docker compose -f compose.yaml -f compose.production.yaml run --rm --entrypoint "\
  rm -rf /etc/letsencrypt/live/$DOMAIN && \
  rm -rf /etc/letsencrypt/archive/$DOMAIN && \
  rm -rf /etc/letsencrypt/renewal/$DOMAIN.conf" certbot

# Request real certificate
echo -e "${YELLOW}### Requesting Let's Encrypt certificate for $DOMAIN...${NC}"
STAGING_ARG=""
if [ "$STAGING" != "0" ]; then
  STAGING_ARG="--staging"
  echo -e "${YELLOW}### Using Let's Encrypt STAGING environment (for testing)${NC}"
fi

docker compose -f compose.yaml -f compose.production.yaml run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $STAGING_ARG \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d $DOMAIN" certbot

# Reload Nginx
echo -e "${YELLOW}### Reloading Nginx...${NC}"
docker compose -f compose.yaml -f compose.production.yaml exec nginx nginx -s reload

echo -e "${GREEN}### SSL certificate successfully obtained!${NC}"
echo -e "${GREEN}### Your site should now be accessible at https://$DOMAIN${NC}"
