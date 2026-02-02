#!/usr/bin/env bash

# Reset/renew Let's Encrypt SSL certificates (when auto-renewal failed)
# Usage:
#   ./bin/reset-certificates.sh              # renew (default domain/email)
#   ./bin/reset-certificates.sh check        # only show certificate status
#   ./bin/reset-certificates.sh <domain> <email>
#
# Defaults: adlab.moreyra.com.ar, facundo@moreyra.com.ar
# Run from project root on the server: cd /opt/laboratory-system
# Requires: Docker, domain pointing to this server, port 80 open.

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

COMMAND="${1:-renew}"
if [[ "$COMMAND" == "check" ]]; then
  echo -e "${YELLOW}### Certificate status:${NC}"
  docker compose -f compose.yaml -f compose.production.yaml run --rm --entrypoint "certbot certificates" certbot
  exit 0
fi

DOMAIN="${1:-adlab.moreyra.com.ar}"
EMAIL="${2:-facundo@moreyra.com.ar}"

echo -e "${YELLOW}### Certificate reset for $DOMAIN${NC}"

# 1. Show current certificate status
echo -e "${YELLOW}### Current certificate status:${NC}"
docker compose -f compose.yaml -f compose.production.yaml run --rm --entrypoint "certbot certificates" certbot 2>/dev/null || true

# 2. Remove existing cert/archive for this domain (fixes "archive directory exists" errors)
echo -e "${YELLOW}### Removing existing certificate data for $DOMAIN (if any)...${NC}"
docker compose -f compose.yaml -f compose.production.yaml run --rm --entrypoint "certbot delete --cert-name $DOMAIN --non-interactive" certbot 2>/dev/null || true

# 3. Request new certificate via webroot (Nginx must be up to serve ACME challenge)
echo -e "${YELLOW}### Requesting certificate (webroot)...${NC}"
docker compose -f compose.yaml -f compose.production.yaml run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN" certbot

# 4. Reload Nginx to use new certs (container name: laboratory-nginx)
echo -e "${YELLOW}### Reloading Nginx...${NC}"
docker exec laboratory-nginx nginx -s reload

echo -e "${GREEN}### Certificates renewed. Check: https://$DOMAIN${NC}"
echo -e "${YELLOW}If renewal failed (e.g. Nginx not running), run full init: ./bin/init-letsencrypt.sh $DOMAIN $EMAIL${NC}"
