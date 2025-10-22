# Email Configuration Guide - AdLab

## Current Setup (Development)

**Status**: ✅ Configured for development  
**Backend**: Console (emails printed to terminal)  
**Cost**: FREE  
**Use case**: Development and testing

---

## Production Configuration Options

### Option 1: Institutional Email (RECOMMENDED) 🏆

**Best for**: University laboratory system

#### Step 1: Contact IT Department
Contact Universidad Nacional del Litoral IT support and request:
- SMTP server address
- SMTP port (usually 587 or 465)
- Email account credentials for the laboratory
- Suggested email: `laboratorio@fcv.unl.edu.ar` or similar

#### Step 2: Update .env File
Edit `/Users/facundomoreyra/pdf-documentation-project/laboratory-system/.env`:

```bash
# Email Configuration (Production - Institutional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.unl.edu.ar  # Get from IT
EMAIL_PORT=587  # Get from IT (587 for TLS, 465 for SSL)
EMAIL_HOST_USER=laboratorio@fcv.unl.edu.ar  # Your institutional email
EMAIL_HOST_PASSWORD=your_password_here  # Secure password from IT
EMAIL_USE_TLS=true  # true for port 587, false for port 465
EMAIL_USE_SSL=false  # false for port 587, true for port 465
DEFAULT_FROM_EMAIL=laboratorio@fcv.unl.edu.ar
SERVER_EMAIL=laboratorio@fcv.unl.edu.ar
```

#### Step 3: Test Email Sending
```bash
docker compose exec web python3 manage.py shell

from django.core.mail import send_mail
send_mail(
    'Test Email - AdLab',
    'This is a test from the laboratory system.',
    'laboratorio@fcv.unl.edu.ar',
    ['your-test-email@example.com'],
    fail_silently=False,
)
```

#### Step 4: Security Considerations
- ✅ Store password in `.env` (never in code)
- ✅ Ensure `.env` is in `.gitignore`
- ✅ Use strong password
- ✅ Enable 2FA if available
- ✅ Request SPF/DKIM configuration from IT for better deliverability

---

### Option 2: SendGrid (Professional Service)

**Best for**: If institutional email not available or needs advanced features

#### Step 1: Sign Up
1. Go to https://sendgrid.com/
2. Create free account (100 emails/day)
3. Verify your email
4. Verify your domain (optional but recommended)

#### Step 2: Create API Key
1. Go to Settings → API Keys
2. Click "Create API Key"
3. Name it "AdLab Production"
4. Choose "Restricted Access" → Full Access for Mail Send
5. Copy the API key (you'll only see it once!)

#### Step 3: Update .env File
```bash
# Email Configuration (Production - SendGrid)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey  # Literally the word "apikey"
EMAIL_HOST_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxx  # Your API key
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
DEFAULT_FROM_EMAIL=laboratorio@yourdomain.com
SERVER_EMAIL=laboratorio@yourdomain.com
```

#### Step 4: Domain Verification (Recommended)
1. In SendGrid: Settings → Sender Authentication
2. Click "Authenticate Your Domain"
3. Follow instructions to add DNS records
4. This improves deliverability significantly

#### Cost:
- FREE: 100 emails/day forever
- Essentials ($15/mo): 50,000 emails/month
- Pro ($90/mo): 100,000 emails/month

---

### Option 3: Gmail SMTP (Quick Testing Only)

**Best for**: Quick testing with real emails (NOT for production)

#### Step 1: Enable App Password
1. Go to Google Account → Security
2. Enable 2-Factor Authentication
3. Go to Security → App Passwords
4. Generate password for "Mail" on "Other"
5. Copy the 16-character password

#### Step 2: Update .env File
```bash
# Email Configuration (Testing - Gmail)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx  # 16-char app password
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
DEFAULT_FROM_EMAIL=your-email@gmail.com
SERVER_EMAIL=your-email@gmail.com
```

**Limitations**:
- ⚠️ 500 emails per day limit
- ⚠️ May go to spam
- ⚠️ Not professional
- ⚠️ NOT recommended for production

---

### Option 4: Amazon SES (High Volume)

**Best for**: Very high volume or AWS infrastructure

#### Cost:
- $0.10 per 1,000 emails
- Very cheap at scale

#### Setup:
1. Create AWS account
2. Set up Amazon SES
3. Verify email/domain
4. Get SMTP credentials
5. Configure .env:

```bash
# Email Configuration (Production - Amazon SES)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com  # Your region
EMAIL_PORT=587
EMAIL_HOST_USER=AKIAIOSFODNN7EXAMPLE  # AWS SMTP credentials
EMAIL_HOST_PASSWORD=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
DEFAULT_FROM_EMAIL=laboratorio@yourdomain.com
SERVER_EMAIL=laboratorio@yourdomain.com
```

---

## Testing Your Configuration

### Method 1: Django Shell
```bash
docker compose exec web python3 manage.py shell

from django.core.mail import send_mail

# Test basic email
send_mail(
    subject='Test Email from AdLab',
    message='This is a test email.',
    from_email='laboratorio@fcv.unl.edu.ar',
    recipient_list=['your-email@example.com'],
    fail_silently=False,
)

# Test HTML email (like verification emails will use)
from django.core.mail import EmailMultiAlternatives

email = EmailMultiAlternatives(
    subject='HTML Test Email from AdLab',
    body='This is the plain text version.',
    from_email='laboratorio@fcv.unl.edu.ar',
    to=['your-email@example.com'],
)
email.attach_alternative('<h1>HTML Test</h1><p>This is the HTML version.</p>', "text/html")
email.send()
```

### Method 2: Management Command
Create a test management command:

```bash
# Test sending verification email
docker compose exec web python3 manage.py shell -c "
from accounts.models import User
from django.core.mail import send_mail

user = User.objects.first()
send_mail(
    'Test Verification Email',
    'This would be your verification link.',
    'laboratorio@fcv.unl.edu.ar',
    [user.email],
)
print('✅ Email sent successfully!')
"
```

---

## Environment Variables Reference

Add these to your `.env` file:

```bash
# ==============================================================================
# EMAIL CONFIGURATION
# ==============================================================================

# Backend: console (dev) or smtp (production)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# SMTP Settings (uncomment for production)
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.yourdomain.com
# EMAIL_PORT=587
# EMAIL_HOST_USER=your-email@yourdomain.com
# EMAIL_HOST_PASSWORD=your-secure-password
# EMAIL_USE_TLS=true
# EMAIL_USE_SSL=false

# Email Addresses
DEFAULT_FROM_EMAIL=noreply@adlab.com
SERVER_EMAIL=server@adlab.com

# Optional: Email timeout settings
# EMAIL_TIMEOUT=10
```

---

## Troubleshooting

### Problem: "Connection refused"
**Solution**: Check EMAIL_HOST and EMAIL_PORT are correct

### Problem: "Authentication failed"
**Solution**: 
- Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
- For Gmail: Use App Password, not regular password
- Check if 2FA is required

### Problem: "TLS/SSL Error"
**Solution**: 
- For port 587: EMAIL_USE_TLS=true, EMAIL_USE_SSL=false
- For port 465: EMAIL_USE_TLS=false, EMAIL_USE_SSL=true

### Problem: Emails go to spam
**Solution**:
- Use institutional/verified domain
- Set up SPF, DKIM, DMARC records
- Use professional email service (SendGrid, SES)
- Don't use Gmail for production

### Problem: "SMTP connection timeout"
**Solution**:
- Check firewall allows outbound connection to EMAIL_PORT
- Try different port (587 vs 465 vs 25)
- Check if server requires authentication

---

## Security Best Practices

1. **Never commit credentials to git**
   - Always use `.env` file
   - Verify `.env` is in `.gitignore`

2. **Use strong passwords**
   - Generate random passwords for email accounts
   - Store securely (password manager)

3. **Enable 2FA when possible**
   - For Gmail/SendGrid/AWS accounts

4. **Use environment-specific credentials**
   - Different credentials for dev/staging/production

5. **Rotate credentials regularly**
   - Change passwords every 3-6 months
   - Especially if team members change

6. **Monitor email sending**
   - Check for unusual sending patterns
   - Set up alerts for failures

---

## Cost Estimation

### For Laboratory Use Case:
Assuming:
- 50 new veterinarian registrations per month
- Each gets 1-2 verification emails
- Plus password resets, notifications, etc.
- **Total: ~200-500 emails/month**

### Recommended Solutions:
1. **Institutional Email**: FREE ✅
2. **SendGrid Free Tier**: FREE (100/day = 3,000/month) ✅
3. **Amazon SES**: $0.10/month ✅

**Conclusion**: You can easily stay within FREE tiers for years.

---

## Next Steps

### For Development (Current):
✅ Already configured - console backend works fine

### For Production:
1. Choose email provider (recommend: institutional)
2. Get credentials
3. Update `.env` file
4. Test with shell commands
5. Deploy and monitor

---

## Need Help?

**For Institutional Email**:
- Contact: UNL IT Support
- Ask for: SMTP configuration for laboratory system

**For SendGrid**:
- Documentation: https://docs.sendgrid.com/for-developers
- Support: support@sendgrid.com

**For Django Email Issues**:
- Django Docs: https://docs.djangoproject.com/en/5.2/topics/email/

---

**Last Updated**: October 11, 2025  
**Version**: 1.0

