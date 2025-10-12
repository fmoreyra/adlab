# Step 13: Production Email Configuration

## Problem Statement

Throughout development, the system uses a console email backend that prints emails to the terminal. This is perfect for development and testing, but before deploying to production, we need to configure a real email service to send notifications to veterinarians and laboratory staff.

The system sends several types of emails:
- **Email verification** (Step 01.1) - Veterinarian registration
- **Password reset** (Step 01) - User account recovery
- **Sample notifications** (Step 08) - Results ready, sample received
- **Report delivery** (Step 06) - PDF report attachments
- **Work order notifications** (Step 07) - Billing information

**Critical Requirement**: Emails must be delivered reliably to ensure veterinarians receive time-sensitive laboratory results and notifications.

---

## Requirements

### Functional Requirements (RF13)

- **RF13.1**: Configure production SMTP server for email delivery
- **RF13.2**: Ensure emails are delivered reliably (>98% delivery rate)
- **RF13.3**: Professional sender address (institutional domain preferred)
- **RF13.4**: HTML email templates render correctly in all major email clients
- **RF13.5**: Email delivery failures are logged and monitored
- **RF13.6**: Support for email attachments (PDF reports)
- **RF13.7**: Configurable email settings via environment variables

### Non-Functional Requirements

- **Reliability**: >98% email delivery rate
- **Performance**: Emails sent within 5 seconds of trigger
- **Security**: Credentials stored securely in environment variables
- **Scalability**: Support for 500-1000 emails/month initially
- **Monitoring**: Track delivery success/failure rates
- **Compliance**: Professional appearance for medical/laboratory context
- **Cost**: Prefer free or low-cost solutions

---

## Email Provider Options

### Option 1: Institutional Email (RECOMMENDED) 🏆

**Provider**: Universidad Nacional del Litoral (UNL) SMTP Server

**Advantages**:
- ✅ **FREE** (included in university services)
- ✅ **Trusted Domain** (@fcv.unl.edu.ar or @unl.edu.ar)
- ✅ **Professional Appearance** - Recipients trust institutional emails
- ✅ **Excellent Deliverability** - Universities have good email reputation
- ✅ **IT Support** - University IT department provides support
- ✅ **No Third-Party Dependencies** - Keep infrastructure internal

**Configuration**:
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.unl.edu.ar  # Get from IT
EMAIL_PORT=587  # Usually 587 (TLS) or 465 (SSL)
EMAIL_HOST_USER=laboratorio@fcv.unl.edu.ar
EMAIL_HOST_PASSWORD=secure_password_here
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL=laboratorio@fcv.unl.edu.ar
```

**Setup Steps**:
1. Contact UNL IT Support
2. Request SMTP credentials for laboratory system
3. Provide justification (critical laboratory notifications)
4. Request email address: `laboratorio@fcv.unl.edu.ar` or similar
5. Get SMTP server, port, username, password
6. Request SPF/DKIM configuration for better deliverability

**Estimated Setup Time**: 1-2 days (depends on IT department response)

---

### Option 2: SendGrid (Professional Service)

**Provider**: SendGrid by Twilio

**Advantages**:
- ✅ **Excellent Deliverability** (99%+ delivery rate)
- ✅ **Easy Setup** (15 minutes)
- ✅ **Email Analytics** (open rates, click rates, bounces)
- ✅ **Free Tier** (100 emails/day = 3,000/month)
- ✅ **Scalable** (easy to upgrade as volume grows)
- ✅ **Professional Templates** and API

**Configuration**:
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey  # Literally "apikey"
EMAIL_HOST_PASSWORD=SG.xxxxxxxxxxxxxxxxxx  # Your API key
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL=laboratorio@yourdomain.com
```

**Pricing**:
- FREE: 100 emails/day (enough for testing and low volume)
- Essentials ($15/month): 50,000 emails/month
- Pro ($90/month): 100,000 emails/month

**Setup Steps**:
1. Sign up at https://sendgrid.com/
2. Verify your email
3. Create API key (Settings → API Keys)
4. (Optional but recommended) Verify domain
5. Configure .env file
6. Test email delivery

**Estimated Setup Time**: 15-30 minutes

---

### Option 3: Amazon SES (High Volume)

**Provider**: Amazon Simple Email Service

**Advantages**:
- ✅ **Very Cheap** ($0.10 per 1,000 emails)
- ✅ **Reliable** (Amazon infrastructure)
- ✅ **Scalable** (handles any volume)
- ✅ **Integration with AWS Services**

**Configuration**:
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_HOST_USER=AKIAIOSFODNN7EXAMPLE
EMAIL_HOST_PASSWORD=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL=laboratorio@yourdomain.com
```

**Pricing**:
- $0.10 per 1,000 emails
- First 62,000 emails FREE (if using EC2)

**Setup Steps**:
1. Create AWS account
2. Set up Amazon SES
3. Verify email/domain
4. Generate SMTP credentials
5. Move out of sandbox mode (request production access)
6. Configure .env file

**Estimated Setup Time**: 1-2 hours (AWS account setup)

---

### Option 4: Gmail SMTP (Testing Only)

**Provider**: Gmail

**⚠️ NOT RECOMMENDED FOR PRODUCTION**

**Only use for**:
- Quick testing with real emails
- Personal projects
- Very low volume (<100 emails/day)

**Limitations**:
- ❌ 500 emails/day limit
- ❌ May go to spam folder
- ❌ Not professional appearance
- ❌ Can be blocked by Google at any time
- ❌ Requires 2FA and app password

**Configuration**:
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx  # App password
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

---

## Recommended Solution

### For This Laboratory System: **Institutional Email (Option 1)**

**Rationale**:
1. **Zero Cost** - Already paid for through university
2. **Trusted Source** - Recipients trust @fcv.unl.edu.ar emails
3. **Professional** - Appropriate for medical/laboratory context
4. **Supported** - IT department can help with issues
5. **Simple** - Just SMTP configuration, no third-party accounts

**Fallback**: If institutional email is not available or has restrictions, use **SendGrid (Option 2)** with free tier.

---

## Implementation Guide

### Phase 1: Obtain Credentials (Before Production)

#### For Institutional Email:
1. **Draft Request Email** to IT Support:
```
Subject: Solicitud de Configuración SMTP para Sistema de Laboratorio

Estimados,

El Laboratorio de Anatomía Patológica de la Facultad de Ciencias 
Veterinarias está implementando un sistema informático para la gestión 
de muestras y resultados.

Necesitamos configurar el envío de emails automáticos para:
- Verificación de cuentas de veterinarios
- Notificaciones de resultados listos
- Envío de informes histopatológicos
- Recuperación de contraseñas

Volumen estimado: 200-500 emails mensuales

Solicitamos:
1. Dirección de email: laboratorio@fcv.unl.edu.ar (o similar)
2. Credenciales SMTP (servidor, puerto, usuario, contraseña)
3. Configuración SPF/DKIM si es posible

¿Podrían asistirnos con esta configuración?

Saludos cordiales,
[Your Name]
Laboratorio de Anatomía Patológica - FCV UNL
```

2. **Wait for Response** (typically 1-3 business days)

3. **Receive Credentials**:
   - SMTP server (e.g., smtp.unl.edu.ar)
   - Port (587 or 465)
   - Username (e.g., laboratorio@fcv.unl.edu.ar)
   - Password (secure password)
   - TLS/SSL settings

#### For SendGrid (Alternative):
1. Go to https://sendgrid.com/
2. Sign up with your email
3. Verify your email address
4. Navigate to Settings → API Keys
5. Create API Key with "Mail Send" permissions
6. Copy API key (shown only once!)
7. (Recommended) Verify domain in Sender Authentication

---

### Phase 2: Update Configuration

#### Step 1: Update .env File

Open `.env` file and update email settings:

```bash
# ==============================================================================
# EMAIL CONFIGURATION - PRODUCTION
# ==============================================================================

# Switch from console to SMTP backend
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# SMTP Server Configuration (update with your credentials)
EMAIL_HOST=smtp.unl.edu.ar
EMAIL_PORT=587
EMAIL_HOST_USER=laboratorio@fcv.unl.edu.ar
EMAIL_HOST_PASSWORD=your_secure_password_here
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false

# Sender Information
DEFAULT_FROM_EMAIL=laboratorio@fcv.unl.edu.ar
SERVER_EMAIL=laboratorio@fcv.unl.edu.ar

# Optional: Timeout (seconds)
EMAIL_TIMEOUT=10
```

#### Step 2: Verify .env is Not in Git

```bash
# Check .gitignore includes .env
cat .gitignore | grep "\.env"

# Should output: .env
# If not, add it:
echo ".env" >> .gitignore
```

#### Step 3: Update Production Environment

For production deployment, ensure environment variables are set in:
- Docker Compose production file
- Environment secrets (if using CI/CD)
- Server environment configuration

---

### Phase 3: Testing

#### Test 1: Basic Email Sending

```bash
docker compose exec web python3 manage.py shell

from django.core.mail import send_mail

send_mail(
    subject='Test Email - AdLab System',
    message='This is a test email from the laboratory system.',
    from_email='laboratorio@fcv.unl.edu.ar',
    recipient_list=['your-test-email@example.com'],
    fail_silently=False,
)

# Should complete without errors
print('✅ Email sent successfully!')
```

#### Test 2: HTML Email (Like Verification Emails)

```bash
from django.core.mail import EmailMultiAlternatives

email = EmailMultiAlternatives(
    subject='Test HTML Email - AdLab',
    body='Plain text version of the email.',
    from_email='laboratorio@fcv.unl.edu.ar',
    to=['your-test-email@example.com'],
)

html_content = '''
<html>
<body>
    <h2 style="color: #2563eb;">Test Email</h2>
    <p>This is an <strong>HTML</strong> test email.</p>
    <p>If you can read this with formatting, HTML emails work!</p>
</body>
</html>
'''

email.attach_alternative(html_content, "text/html")
email.send()

print('✅ HTML email sent!')
```

#### Test 3: Email with Attachment (Like Reports)

```bash
from django.core.mail import EmailMessage

email = EmailMessage(
    subject='Test Email with Attachment',
    body='This email has a test attachment.',
    from_email='laboratorio@fcv.unl.edu.ar',
    to=['your-test-email@example.com'],
)

# Create a simple test file
email.attach('test.txt', 'This is a test attachment content.', 'text/plain')
email.send()

print('✅ Email with attachment sent!')
```

#### Test 4: Verify Email Templates

Test actual system emails:

```bash
# Test password reset email
from accounts.models import User
from django.test.utils import override_settings

user = User.objects.first()
# Trigger password reset
# Check inbox for formatted email
```

#### Test 5: Multiple Recipients

```bash
send_mail(
    subject='Test Multiple Recipients',
    message='Testing multiple recipients.',
    from_email='laboratorio@fcv.unl.edu.ar',
    recipient_list=[
        'recipient1@example.com',
        'recipient2@example.com',
        'recipient3@example.com',
    ],
)

print('✅ Multiple recipient email sent!')
```

---

### Phase 4: Monitoring & Validation

#### Check Email Logs

```bash
# View Django logs for email sending
docker compose logs web | grep -i email

# Look for:
# - "Email sent successfully"
# - Any SMTP errors
# - Connection issues
```

#### Monitor Deliverability

**Check Inbox**:
- ✅ Email received
- ✅ Not in spam folder
- ✅ HTML renders correctly
- ✅ Links work
- ✅ Attachments open correctly

**Test Different Email Providers**:
- Gmail
- Outlook/Hotmail
- Yahoo Mail
- Institutional emails

**Check Spam Score** (optional):
- Use Mail-Tester.com
- Send test email to check@mail-tester.com
- Review spam score (aim for 9-10/10)

---

## Security Best Practices

### 1. Secure Credential Storage

```bash
# NEVER commit credentials to git
# Always use environment variables

# Good ✅
EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}

# Bad ❌ (hardcoded in code)
EMAIL_HOST_PASSWORD = "mypassword123"
```

### 2. File Permissions

```bash
# Ensure .env file is not readable by others
chmod 600 .env

# Check permissions
ls -la .env
# Should show: -rw------- (only owner can read/write)
```

### 3. Rotate Credentials

```bash
# Change email password every 3-6 months
# Update .env file
# Restart services
docker compose restart web
```

### 4. Use Strong Passwords

```bash
# Generate strong password
openssl rand -base64 32

# Or use password manager
# Minimum 16 characters, random
```

### 5. Enable 2FA

If using SendGrid, Gmail, or AWS:
- Enable two-factor authentication on account
- Use API keys instead of passwords where possible

---

## Troubleshooting

### Problem: Connection Refused

**Symptoms**: 
```
Connection refused at smtp.server.com:587
```

**Solutions**:
1. Verify EMAIL_HOST and EMAIL_PORT are correct
2. Check firewall allows outbound connections to port 587
3. Try alternative port (25, 465, 587, 2525)
4. Check server is accessible: `telnet smtp.server.com 587`

---

### Problem: Authentication Failed

**Symptoms**:
```
535 Authentication failed
```

**Solutions**:
1. Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
2. For Gmail: Use App Password, not regular password
3. Check if account requires 2FA
4. Verify account is not locked/disabled

---

### Problem: TLS/SSL Error

**Symptoms**:
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solutions**:
1. For port 587: Set EMAIL_USE_TLS=true, EMAIL_USE_SSL=false
2. For port 465: Set EMAIL_USE_TLS=false, EMAIL_USE_SSL=true
3. Check server supports TLS/SSL on that port

---

### Problem: Emails Go to Spam

**Solutions**:
1. Use institutional/verified domain
2. Set up SPF record: `v=spf1 include:_spf.google.com ~all`
3. Set up DKIM signing (ask IT department)
4. Set up DMARC policy
5. Avoid spam trigger words in subject/body
6. Use professional email service (not Gmail)
7. Request domain verification from email provider

---

### Problem: Timeout

**Symptoms**:
```
SMTPServerDisconnected: Connection unexpectedly closed
```

**Solutions**:
1. Increase EMAIL_TIMEOUT setting (default: 10 seconds)
2. Check network connectivity
3. Verify server is responsive
4. Try different EMAIL_HOST if available

---

## Success Metrics

After configuration, monitor these metrics:

### Email Delivery Rate
**Target**: >98%  
**Measure**: Successful sends / Total attempts

### Email Open Rate (if using SendGrid)
**Target**: >40%  
**Measure**: Opened emails / Delivered emails

### Spam Rate
**Target**: <1%  
**Measure**: Spam reports / Delivered emails

### Response Time
**Target**: <5 seconds  
**Measure**: Time from trigger to email sent

### Bounce Rate
**Target**: <2%  
**Measure**: Bounced emails / Total sent

---

## Cost Analysis

### Estimated Email Volume for Laboratory

**Monthly Email Breakdown**:
- New veterinarian registrations: ~20-50 emails
- Email verifications (including resends): ~30-70 emails
- Password resets: ~10-20 emails
- Sample received notifications: ~50-100 emails
- Results ready notifications: ~50-100 emails
- Report delivery emails: ~50-100 emails
- Miscellaneous notifications: ~20-50 emails

**Total Estimated**: 200-500 emails/month

### Cost Comparison

| Provider | Monthly Cost | Emails Included | Cost Per Email |
|----------|--------------|-----------------|----------------|
| **Institutional (UNL)** | **FREE** | Unlimited* | $0.00 |
| **SendGrid Free** | **FREE** | 3,000 | $0.00 |
| SendGrid Essentials | $15 | 50,000 | $0.0003 |
| Amazon SES | ~$0.05 | 500 | $0.0001 |
| Gmail | FREE | 15,000 | $0.00 (not recommended) |

*Within reasonable limits

**Recommendation**: Start with FREE options (institutional or SendGrid free tier). You're well within free limits for foreseeable future.

---

## Deployment Checklist

### Before Production Deployment

- [ ] Email credentials obtained (institutional or SendGrid)
- [ ] .env file updated with production SMTP settings
- [ ] .env file not in git (verify .gitignore)
- [ ] Email sending tested successfully
- [ ] HTML emails render correctly in test inboxes
- [ ] Emails not going to spam
- [ ] Email attachments work (test with PDF)
- [ ] Multiple recipients tested
- [ ] SPF/DKIM configured (if institutional)
- [ ] Domain verified (if using SendGrid)
- [ ] Monitoring/logging configured
- [ ] Error handling tested (what happens if email fails?)
- [ ] Credentials stored securely in production environment

### Production Validation

- [ ] Send test verification email to real veterinarian
- [ ] Send test password reset email
- [ ] Send test notification email
- [ ] Verify all emails arrive within 1 minute
- [ ] Check spam folders
- [ ] Test from different email clients (Gmail, Outlook)
- [ ] Test on mobile devices
- [ ] Monitor logs for first 24 hours
- [ ] Have rollback plan ready (can revert to console backend)

---

## Rollback Plan

If email sending fails in production:

### Step 1: Identify Issue
```bash
# Check logs
docker compose logs web | grep -i email | tail -50

# Common issues:
# - Authentication failed
# - Connection timeout
# - Invalid credentials
```

### Step 2: Temporary Fallback (if critical)
```bash
# Revert to console backend temporarily
# Edit .env:
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Restart services
docker compose restart web

# Note: Emails will print to logs but not send
# Gives you time to fix the issue
```

### Step 3: Fix and Redeploy
```bash
# Fix configuration
# Update .env with correct settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# Restart
docker compose restart web

# Test immediately
docker compose exec web python3 manage.py shell
# ... test email sending ...
```

---

## Alternative: Asynchronous Email with Celery

For better performance (especially with attachments), consider sending emails asynchronously using Celery (already configured in your system).

### Benefits:
- ✅ Non-blocking - User doesn't wait for email to send
- ✅ Retry logic - Automatically retry failed emails
- ✅ Better error handling
- ✅ Can batch emails

### Implementation (Future Enhancement):
```python
# Create celery task
from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_email_async(subject, message, from_email, recipient_list):
    send_mail(subject, message, from_email, recipient_list)
    
# Use in views
send_email_async.delay(
    'Subject',
    'Message',
    'from@example.com',
    ['to@example.com']
)
```

**Note**: This is an optional enhancement for Step 13 if needed.

---

## Documentation References

- Django Email Documentation: https://docs.djangoproject.com/en/5.2/topics/email/
- SendGrid Django Guide: https://docs.sendgrid.com/for-developers/sending-email/django
- Amazon SES with Django: https://docs.aws.amazon.com/ses/latest/dg/send-email-smtp.html
- EMAIL_CONFIGURATION_GUIDE.md (detailed setup guide in project root)

---

## Acceptance Criteria

- [ ] ✅ Email provider selected and credentials obtained
- [ ] ✅ Production SMTP configured in .env file
- [ ] ✅ Test emails delivered successfully (>98% rate)
- [ ] ✅ HTML emails render correctly in major email clients
- [ ] ✅ Emails not going to spam (<1% spam rate)
- [ ] ✅ Email attachments work (tested with PDF)
- [ ] ✅ Credentials stored securely (not in git)
- [ ] ✅ Monitoring/logging configured
- [ ] ✅ Error handling tested
- [ ] ✅ Rollback plan documented and tested
- [ ] ✅ Team trained on email configuration

---

## Dependencies

### Must be completed first:
- Step 01: Authentication & User Management (uses password reset emails)
- Step 01.1: Email Verification (requires email sending)
- Step 06: Report Generation (may send reports via email)
- Step 08: Email Notifications (requires email sending)

### Blocks these steps:
- Production deployment (cannot deploy without email)
- User acceptance testing with real veterinarians

---

## Estimated Effort

**Time**: 1-3 days

**Breakdown**:
- Obtaining credentials (institutional): 1-2 days (waiting for IT)
- Configuration and testing: 2-4 hours
- Troubleshooting and validation: 2-4 hours
- Documentation and team training: 1-2 hours

**Note**: If using SendGrid or similar service instead of institutional email, can be completed in 1-2 hours.

---

## Notes

- Email configuration should be one of the **last steps** before production
- Test thoroughly with real email addresses
- Keep console backend for development/staging environments
- Consider using different email providers for different environments (dev/staging/prod)
- Monitor delivery rates closely in first week of production
- Have IT department contact info ready for troubleshooting

---

**Status**: 📝 Documented - To be implemented before production deployment  
**Priority**: HIGH (required for production)  
**Risk**: LOW (well-understood technology, multiple fallback options)

