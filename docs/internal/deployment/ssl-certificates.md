# SSL Certificate Setup - Tomorrow's Task

## 🎯 **Objective**
Get production Let's Encrypt SSL certificates to replace the temporary self-signed certificates.

## ⏰ **When to Run**
**Date**: October 20, 2025  
**Time**: After 10:30:38 UTC (when rate limit resets)  
**Current Rate Limit**: 5 certificates issued in last 168 hours (resets at 2025-10-20 10:30:38 UTC)

## 🔧 **Prerequisites**
- ✅ Volume mounting issue is FIXED (read-write access)
- ✅ Nginx container running with proper volume mounts
- ✅ Domain `adlab.moreyra.com.ar` resolving to `147.93.7.60`
- ✅ HTTP site working and accessible

## 📋 **Step-by-Step Instructions**

### 1. **Stop Nginx Temporarily**
```bash
ssh root@147.93.7.60 "docker stop laboratory-nginx"
```

### 2. **Generate Production Certificates**
```bash
ssh root@147.93.7.60 "cd /opt/laboratory-system && certbot certonly --standalone -d adlab.moreyra.com.ar --email facundo@moreyra.com.ar --agree-tos --no-eff-email --config-dir certbot/conf --work-dir certbot/work --logs-dir certbot/logs"
```

### 3. **Verify Certificates Were Created**
```bash
ssh root@147.93.7.60 "cd /opt/laboratory-system && ls -la certbot/conf/live/adlab.moreyra.com.ar/"
```

**Expected output:**
```
-rw-r--r-- 1 root root 1234 fullchain.pem
-rw------- 1 root root 1704 privkey.pem
```

### 4. **Verify Certificate Details**
```bash
ssh root@147.93.7.60 "cd /opt/laboratory-system && openssl x509 -in certbot/conf/live/adlab.moreyra.com.ar/fullchain.pem -text -noout | grep -A 2 -B 2 'Issuer\|Subject\|Not After'"
```

**Expected output:**
```
Issuer: C=US, O=Let's Encrypt, CN=R3
Subject: CN=adlab.moreyra.com.ar
Not After: Jan 16 23:XX:XX 2026 GMT
```

### 5. **Start Nginx with Production Certificates**
```bash
ssh root@147.93.7.60 "docker start laboratory-nginx"
```

### 6. **Test HTTPS Connection**
```bash
curl -I https://adlab.moreyra.com.ar/
```

**Expected output:**
```
HTTP/2 200
server: nginx/1.25.5
strict-transport-security: max-age=31536000; includeSubDomains
```

### 7. **Test in Browser**
- Open Chrome
- Navigate to `https://adlab.moreyra.com.ar/`
- **Should work without security warnings!** ✅

## 🔍 **Troubleshooting**

### **If Rate Limit Still Active:**
```
Error: too many certificates (5) already issued for this exact set of identifiers
```
**Solution**: Wait until after 10:30:38 UTC

### **If Certificates Don't Persist:**
```bash
# Check volume mount
ssh root@147.93.7.60 "docker inspect laboratory-nginx | grep -A 5 -B 5 'letsencrypt'"
```
**Should show**: `"Mode": "rw"` (not `"ro"`)

### **If Nginx Won't Start:**
```bash
# Check nginx configuration
ssh root@147.93.7.60 "docker exec laboratory-nginx nginx -t"
```

### **If HTTPS Still Shows Self-Signed:**
```bash
# Check certificate content
ssh root@147.93.7.60 "cd /opt/laboratory-system && openssl x509 -in certbot/conf/live/adlab.moreyra.com.ar/fullchain.pem -text -noout | grep Issuer"
```
**Should show**: `Issuer: C=US, O=Let's Encrypt, CN=R3`

## 🎉 **Success Indicators**

- ✅ **Chrome**: No security warnings
- ✅ **Certificate**: Shows "Let's Encrypt" as issuer
- ✅ **HTTPS**: HTTP/2 200 response
- ✅ **Security Headers**: All present
- ✅ **Expiry**: Valid until 2026-01-16

## 📝 **Post-Setup Tasks**

### **Set Up Auto-Renewal**
```bash
ssh root@147.93.7.60 "cd /opt/laboratory-system && certbot renew --dry-run"
```

### **Add to Crontab (Optional)**
```bash
ssh root@147.93.7.60 "crontab -e"
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🚨 **Important Notes**

1. **Rate Limit**: Only 5 certificates per domain per 168 hours
2. **Volume Mounts**: Must be read-write (`rw`) not read-only (`ro`)
3. **Nginx Stop**: Required during certificate generation (port 80 conflict)
4. **Domain Resolution**: Must point to `147.93.7.60`
5. **Email**: `facundo@moreyra.com.ar` is registered with Let's Encrypt

## 📞 **If Issues Persist**

1. Check rate limit status: `certbot certificates`
2. Verify domain resolution: `nslookup adlab.moreyra.com.ar`
3. Check nginx logs: `docker logs laboratory-nginx`
4. Verify volume mounts: `docker inspect laboratory-nginx`

---

**Created**: October 19, 2025  
**Rate Limit Reset**: October 20, 2025 10:30:38 UTC  
**Status**: Ready to execute ✅
