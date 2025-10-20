# Troubleshooting: Django 500 Error - Missing Static Files Manifest

## 🚨 **Problem Description**

**Error**: Django application returning 500 Internal Server Error on all endpoints except `/up/` health check.

**Symptoms**:
- Homepage returns 500 error
- Admin interface works (302 redirects)
- Health check endpoint `/up/` works fine
- Error occurs in both direct Django access and through Nginx

## 🔍 **Root Cause Analysis**

### Error Details
```
ValueError: Missing staticfiles manifest entry for 'images/logo-unl-fcv.png'
```

### Technical Cause
- **WhiteNoise Configuration**: Using `whitenoise.storage.CompressedManifestStaticFilesStorage`
- **Missing Manifest**: The `staticfiles.json` manifest file was missing from `/public_collected/`
- **Template Rendering**: Django templates using `{% static %}` tags couldn't resolve static file paths

### Why This Happened
1. **WhiteNoise Manifest Storage**: Requires a manifest file to map original filenames to hashed versions
2. **Missing collectstatic**: The `staticfiles.json` manifest wasn't generated during deployment
3. **Template Dependencies**: Homepage template uses static files (logo, CSS, JS) that require the manifest

## 🛠️ **Solution Steps**

### 1. Identify the Problem
```bash
# Test Django directly
curl http://localhost:8000/  # Returns 500

# Check Django logs
docker logs laboratory-web-1 --tail 10

# Use Django shell to get detailed error
docker exec laboratory-web-1 python manage.py shell -c "
from django.test import Client; 
c = Client(); 
response = c.get('/'); 
print('Status:', response.status_code)
"
```

### 2. Fix the Issue
```bash
# Regenerate static files manifest
docker exec laboratory-web-1 python manage.py collectstatic --no-input --clear

# Restart Django service
docker restart laboratory-web-1

# Wait for service to start
sleep 10

# Test the fix
curl -I http://localhost:8000/  # Should return 200 OK
```

### 3. Verify Through Nginx
```bash
# Test through reverse proxy
curl -I http://147.93.7.60/  # Should return 200 OK
```

## 📁 **Files Affected**

### Runtime Files (No Source Code Changes)
- **Created**: `/public_collected/staticfiles.json` (inside container)
- **Updated**: Static files in `/public_collected/` directory
- **No changes**: Source code, configuration files, or git repository

### Current WhiteNoise Configuration
```python
# src/config/settings.py
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

## 🔧 **Prevention for Future Deployments**

### 1. Ensure collectstatic in Deployment
Add to deployment scripts:
```bash
# Always run collectstatic during deployment
docker exec laboratory-web-1 python manage.py collectstatic --no-input
```

### 2. Docker Compose Integration
Consider adding to `compose.production.yaml`:
```yaml
services:
  web:
    # ... existing config ...
    command: >
      sh -c "python manage.py collectstatic --no-input &&
             python manage.py migrate &&
             gunicorn config.wsgi:application --bind 0.0.0.0:8000"
```

### 3. Health Check Verification
Add static files check to health check:
```python
# In up/views.py or similar
def health_check(request):
    try:
        # Test static files manifest
        from django.contrib.staticfiles.storage import staticfiles_storage
        staticfiles_storage.url('images/logo-unl-fcv.png')
        return JsonResponse({'status': 'healthy'})
    except Exception as e:
        return JsonResponse({'status': 'unhealthy', 'error': str(e)}, status=500)
```

## 🧪 **Testing the Fix**

### 1. Verify Static Files Manifest
```bash
# Check if manifest exists
docker exec laboratory-web-1 ls -la /public_collected/staticfiles.json

# Check manifest content
docker exec laboratory-web-1 head -5 /public_collected/staticfiles.json
```

### 2. Test Static File Resolution
```bash
# Test in Django shell
docker exec laboratory-web-1 python manage.py shell -c "
from django.contrib.staticfiles.storage import staticfiles_storage
print('Logo URL:', staticfiles_storage.url('images/logo-unl-fcv.png'))
"
```

### 3. End-to-End Testing
```bash
# Test all endpoints
curl -I http://147.93.7.60/           # Homepage
curl -I http://147.93.7.60/admin/     # Admin
curl -I http://147.93.7.60/up/        # Health check
```

## 📊 **Manifest File Structure**

The `staticfiles.json` contains mappings like:
```json
{
  "paths": {
    "images/logo-unl-fcv.png": "images/logo-unl-fcv.f8960d72d35b.png",
    "css/app.css": "css/app.1f678856dcd0.css",
    "js/app.js": "js/app.ee4a59b5e269.js"
  },
  "version": "1.1",
  "hash": "14ad9286699a"
}
```

## 🚨 **Warning Signs to Watch For**

1. **500 errors on pages with static content** (CSS, images, JS)
2. **Admin interface works but main site doesn't**
3. **Health check works but homepage fails**
4. **Error messages mentioning "Missing staticfiles manifest entry"**

## 🔄 **Recovery Commands (Quick Reference)**

```bash
# Quick fix for missing static files manifest
docker exec laboratory-web-1 python manage.py collectstatic --no-input --clear
docker restart laboratory-web-1
sleep 10
curl -I http://147.93.7.60/  # Verify fix
```

## 📝 **Notes**

- **No git commits needed** - this is a runtime data issue, not a code issue
- **WhiteNoise manifest storage** requires the manifest file for production
- **collectstatic must be run** during deployment to generate the manifest
- **This issue can occur** if the container is rebuilt without running collectstatic

---

**Date**: October 19, 2025  
**Environment**: Production (147.93.7.60)  
**Django Version**: 5.2.1  
**WhiteNoise Version**: Latest  
**Status**: ✅ Resolved
