# Nginx Configuration for Production

This directory contains Nginx configuration for production deployment.

## Files

- `nginx.conf` - Main Nginx configuration
- `conf.d/laboratory.conf.template` - Site configuration template
- `conf.d/laboratory.conf` - Generated site configuration (not in git)

## Setup

The `laboratory.conf` file is generated automatically by the `init-letsencrypt.sh` script.

Do not edit `laboratory.conf` directly. Instead, modify the template and regenerate:

```bash
sed "s/DOMAIN_PLACEHOLDER/your-domain.com/g" nginx/conf.d/laboratory.conf.template > nginx/conf.d/laboratory.conf
```

## Manual Configuration

If you need to customize Nginx configuration:

1. Edit `nginx.conf` or `laboratory.conf.template`
2. Regenerate `laboratory.conf` if needed
3. Reload Nginx: `docker compose -f compose.yaml -f compose.production.yaml exec nginx nginx -s reload`
4. Commit changes to git
