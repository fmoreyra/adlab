# Step 08: Email Notifications (Celery + Redis Queue)

## Problem Statement

The laboratory needs to keep veterinarians informed about the status of their samples throughout the analysis process. Currently, communication is ad-hoc and relies on phone calls or manual emails. Additionally, the system already has email-sending code scattered across different modules (email verification, password resets, etc.). 

We need a centralized, robust email notification system using Celery with Redis as the message broker. This will provide:
- Asynchronous email delivery (non-blocking)
- Automatic retry on failure
- Centralized email-sending logic
- Scalable architecture
- Task monitoring and tracking

All existing email-sending code will be refactored to use this queue system.

## Requirements

### Functional Requirements

- **Celery + Redis Infrastructure:**
  - Celery workers for async email processing
  - Redis as message broker
  - Task retry mechanism with exponential backoff
  - Task result backend for tracking
  
- **Email Types (Context-Based):**
  - Email verification (Step 01)
  - Password reset (Step 01)
  - Sample reception notification
  - Report ready notification
  - Work order notification
  - Custom admin notifications
  
- **Features:**
  - Unified `send_email` Celery task
  - Context-based email templates
  - Attachment support (PDFs)
  - Notification preferences per veterinarian
  - Email history tracking
  - Retry on failure (automatic via Celery)
  
- **Refactoring:**
  - Replace all existing `send_mail()` calls with Celery tasks
  - Centralize email configuration
  - Standardize email templates

### Non-Functional Requirements

- **Deliverability**: 98%+ success rate
- **Speed**: Emails queued immediately, sent within seconds by workers
- **Reliability**: Celery automatic retry (max 3 attempts, exponential backoff)
- **Scalability**: Multiple Celery workers can be added
- **Monitoring**: Celery Flower for task monitoring
- **Privacy**: No sensitive data in email body (only in attachments)

## Data Model

### Celery Task Tracking (Built-in)

Celery with Redis result backend automatically tracks:
- Task ID (UUID)
- Task status (PENDING, STARTED, SUCCESS, FAILURE, RETRY)
- Task result or exception
- Task timestamps
- Retry count

No custom table needed for task status!

### New Model: EmailLog

```python
class EmailLog(models.Model):
    """
    High-level email logging for business records.
    Complements Celery's task tracking.
    """
    
    class EmailType(models.TextChoices):
        EMAIL_VERIFICATION = 'email_verification', 'Email Verification'
        PASSWORD_RESET = 'password_reset', 'Password Reset'
        SAMPLE_RECEPTION = 'sample_reception', 'Sample Reception'
        REPORT_READY = 'report_ready', 'Report Ready'
        WORK_ORDER = 'work_order', 'Work Order'
        CUSTOM = 'custom', 'Custom Notification'
    
    class Status(models.TextChoices):
        QUEUED = 'queued', 'Queued'
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'
        BOUNCED = 'bounced', 'Bounced'
    
    # Email details
    email_type = models.CharField(max_length=50, choices=EmailType.choices)
    recipient_email = models.EmailField()
    recipient = models.ForeignKey('accounts.Veterinarian', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='emails_received')
    subject = models.CharField(max_length=500)
    
    # Related objects
    protocol = models.ForeignKey('protocols.Protocol', on_delete=models.SET_NULL,
                                 null=True, blank=True)
    work_order = models.ForeignKey('protocols.WorkOrder', on_delete=models.SET_NULL,
                                    null=True, blank=True)
    
    # Celery task tracking
    celery_task_id = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Metadata
    has_attachment = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Email Log"
        verbose_name_plural = "Email Logs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email_type', '-created_at']),
            models.Index(fields=['recipient_email', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.email_type} to {self.recipient_email} ({self.status})"
```

### New Model: NotificationPreference

```python
class NotificationPreference(models.Model):
    """
    Per-veterinarian notification preferences.
    """
    
    veterinarian = models.OneToOneField('accounts.Veterinarian', on_delete=models.CASCADE,
                                        related_name='notification_preferences')
    
    # Preferences
    notify_on_reception = models.BooleanField(default=True,
                                              help_text="Notify when sample is received")
    notify_on_processing = models.BooleanField(default=False,
                                               help_text="Notify on status changes")
    notify_on_report_ready = models.BooleanField(default=True,
                                                  help_text="Notify when report is ready")
    
    # Alternative email
    alternative_email = models.EmailField(blank=True,
                                          help_text="Send notifications to this email instead")
    
    # Attachment preferences
    include_attachments = models.BooleanField(default=True,
                                              help_text="Include PDFs in emails")
    
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"
    
    def __str__(self):
        return f"Preferences for {self.veterinarian.user.email}"
    
    def get_recipient_email(self):
        """Get the email to send to (alternative or default)."""
        return self.alternative_email or self.veterinarian.user.email
    
    def should_send(self, email_type):
        """Check if notification should be sent for this type."""
        type_map = {
            'sample_reception': self.notify_on_reception,
            'report_ready': self.notify_on_report_ready,
            'processing': self.notify_on_processing,
        }
        return type_map.get(email_type, True)  # Default to True for other types
```

### Email Templates (Django Templates)

Templates stored as files in `templates/emails/`:
- `emails/verification.html`
- `emails/password_reset.html`
- `emails/sample_reception.html`
- `emails/report_ready.html`
- `emails/work_order.html`

No database table needed - Django template loader handles this!

## Celery Configuration

### Redis Setup

```python
# settings.py

# Redis configuration
REDIS_HOST = env('REDIS_HOST', default='localhost')
REDIS_PORT = env.int('REDIS_PORT', default=6379)
REDIS_DB = env.int('REDIS_DB', default=0)
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

# Celery configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Argentina/Buenos_Aires'

# Task configuration
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes

# Retry configuration
CELERY_TASK_ACKS_LATE = True  # Tasks acknowledged after completion
CELERY_TASK_REJECT_ON_WORKER_LOST = True
```

### Celery App

```python
# config/celery.py
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('laboratory')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

## Celery Task Design

### Main Task: send_email

```python
# protocols/tasks.py (or emails/tasks.py)
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import EmailLog
import logging

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    autoretry_for=(Exception,),
    retry_backoff=True,  # Exponential backoff
    retry_backoff_max=600,  # Max 10 minutes
    retry_jitter=True,  # Add randomness to prevent thundering herd
)
def send_email(
    self,
    email_type,
    recipient_email,
    subject,
    context,
    template_name=None,
    attachment_path=None,
    email_log_id=None
):
    """
    Unified email sending task.
    
    Args:
        email_type: Type of email (from EmailLog.EmailType)
        recipient_email: Recipient email address
        subject: Email subject
        context: Template context dict
        template_name: Optional custom template (defaults based on email_type)
        attachment_path: Optional path to PDF attachment
        email_log_id: Optional EmailLog ID for tracking
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    try:
        # Determine template
        if not template_name:
            template_map = {
                'email_verification': 'emails/verification.html',
                'password_reset': 'emails/password_reset.html',
                'sample_reception': 'emails/sample_reception.html',
                'report_ready': 'emails/report_ready.html',
                'work_order': 'emails/work_order.html',
            }
            template_name = template_map.get(email_type, 'emails/default.html')
        
        # Render email HTML
        html_content = render_to_string(template_name, context)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=html_content,  # Fallback plain text
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        email.attach_alternative(html_content, "text/html")
        
        # Add attachment if provided
        if attachment_path:
            email.attach_file(attachment_path)
        
        # Send email
        email.send(fail_silently=False)
        
        # Update EmailLog if provided
        if email_log_id:
            try:
                email_log = EmailLog.objects.get(id=email_log_id)
                email_log.status = EmailLog.Status.SENT
                email_log.sent_at = timezone.now()
                email_log.save()
            except EmailLog.DoesNotExist:
                pass
        
        logger.info(f"Email sent: {email_type} to {recipient_email}")
        
        return {
            'success': True,
            'message': f'Email sent to {recipient_email}',
            'task_id': self.request.id
        }
        
    except Exception as exc:
        # Update EmailLog with error
        if email_log_id:
            try:
                email_log = EmailLog.objects.get(id=email_log_id)
                email_log.status = EmailLog.Status.FAILED
                email_log.error_message = str(exc)
                email_log.save()
            except EmailLog.DoesNotExist:
                pass
        
        logger.error(f"Email failed: {email_type} to {recipient_email} - {exc}")
        
        # Celery will auto-retry based on decorator settings
        raise
```

### Helper Function: Queue Email

```python
# protocols/emails.py (or emails/utils.py)
from django.utils import timezone
from .models import EmailLog, NotificationPreference
from .tasks import send_email

def queue_email(
    email_type,
    recipient_email,
    subject,
    context,
    template_name=None,
    attachment_path=None,
    protocol=None,
    work_order=None,
    veterinarian=None
):
    """
    Queue an email for sending via Celery.
    
    Args:
        email_type: EmailLog.EmailType choice
        recipient_email: Recipient email
        subject: Email subject
        context: Template context
        template_name: Optional custom template
        attachment_path: Optional attachment path
        protocol: Optional Protocol instance
        work_order: Optional WorkOrder instance
        veterinarian: Optional Veterinarian instance
    
    Returns:
        EmailLog: Created email log instance
    """
    # Create EmailLog
    email_log = EmailLog.objects.create(
        email_type=email_type,
        recipient_email=recipient_email,
        recipient=veterinarian,
        subject=subject,
        protocol=protocol,
        work_order=work_order,
        celery_task_id='',  # Will be set after task dispatch
        status=EmailLog.Status.QUEUED,
        has_attachment=bool(attachment_path),
    )
    
    # Dispatch Celery task
    task = send_email.delay(
        email_type=email_type,
        recipient_email=recipient_email,
        subject=subject,
        context=context,
        template_name=template_name,
        attachment_path=attachment_path,
        email_log_id=email_log.id
    )
    
    # Update EmailLog with task ID
    email_log.celery_task_id = task.id
    email_log.save()
    
    return email_log
```

### Specialized Email Functions

```python
# protocols/emails.py

def send_verification_email(user):
    """Send email verification email."""
    from accounts.models import EmailVerificationToken
    
    # Generate token
    token = EmailVerificationToken.objects.create(user=user)
    
    # Queue email
    return queue_email(
        email_type='email_verification',
        recipient_email=user.email,
        subject='Verifique su correo electrónico - LAP UNL',
        context={
            'user': user,
            'verification_url': token.get_verification_url(),
            'token': token.token,
        }
    )

def send_password_reset_email(user, reset_url):
    """Send password reset email."""
    return queue_email(
        email_type='password_reset',
        recipient_email=user.email,
        subject='Restablezca su contraseña - LAP UNL',
        context={
            'user': user,
            'reset_url': reset_url,
        }
    )

def send_sample_reception_notification(protocol):
    """Send sample reception notification."""
    veterinarian = protocol.veterinarian
    
    # Check preferences
    prefs, _ = NotificationPreference.objects.get_or_create(veterinarian=veterinarian)
    if not prefs.should_send('sample_reception'):
        return None
    
    recipient_email = prefs.get_recipient_email()
    
    return queue_email(
        email_type='sample_reception',
        recipient_email=recipient_email,
        subject=f'Muestra recibida - Protocolo {protocol.protocol_number}',
        context={
            'protocol': protocol,
            'veterinarian': veterinarian,
        },
        protocol=protocol,
        veterinarian=veterinarian
    )

def send_report_ready_notification(protocol, report_pdf_path=None):
    """Send report ready notification with PDF attachment."""
    veterinarian = protocol.veterinarian
    
    # Check preferences
    prefs, _ = NotificationPreference.objects.get_or_create(veterinarian=veterinarian)
    if not prefs.should_send('report_ready'):
        return None
    
    recipient_email = prefs.get_recipient_email()
    attachment = report_pdf_path if prefs.include_attachments else None
    
    return queue_email(
        email_type='report_ready',
        recipient_email=recipient_email,
        subject=f'Informe disponible - Protocolo {protocol.protocol_number}',
        context={
            'protocol': protocol,
            'veterinarian': veterinarian,
            'report': protocol.report,
        },
        attachment_path=attachment,
        protocol=protocol,
        veterinarian=veterinarian
    )

def send_work_order_notification(work_order, pdf_path=None):
    """Send work order notification."""
    veterinarian = work_order.veterinarian
    
    recipient_email = veterinarian.user.email
    
    return queue_email(
        email_type='work_order',
        recipient_email=recipient_email,
        subject=f'Orden de Trabajo {work_order.order_number}',
        context={
            'work_order': work_order,
            'veterinarian': veterinarian,
        },
        attachment_path=pdf_path,
        work_order=work_order,
        veterinarian=veterinarian
    )
```

## Refactoring Existing Email Code

### Before: Step 01 Email Verification (Old Code)

```python
# accounts/views.py (OLD - TO BE REFACTORED)
from django.core.mail import send_mail

def send_verification_email_old(user, token):
    """Old synchronous email sending."""
    subject = 'Verify your email'
    message = f'Click here: http://example.com/verify/{token}'
    send_mail(
        subject,
        message,
        'noreply@lab.com',
        [user.email],
        fail_silently=False,
    )
```

### After: Using Celery Queue

```python
# accounts/views.py (NEW - REFACTORED)
from protocols.emails import send_verification_email

def register_view(request):
    # ... user creation logic ...
    
    # Queue email asynchronously
    send_verification_email(user)
    
    messages.success(request, 'Verification email sent!')
    # View returns immediately, email sent in background
```

### Before: Step 06 Report Sent (Old Code)

```python
# protocols/views.py (OLD)
def send_report_view(request, protocol_id):
    protocol = get_object_or_404(Protocol, id=protocol_id)
    
    # Generate PDF
    pdf_path = generate_report_pdf(protocol)
    
    # Send email synchronously - BLOCKS the view!
    send_mail(
        subject=f'Report ready - {protocol.protocol_number}',
        message='Your report is ready',
        from_email='lab@unl.edu.ar',
        recipient_list=[protocol.veterinarian.user.email],
    )
    
    return redirect('protocol_detail', protocol_id=protocol_id)
```

### After: Using Celery Queue

```python
# protocols/views.py (NEW)
from .emails import send_report_ready_notification

def send_report_view(request, protocol_id):
    protocol = get_object_or_404(Protocol, id=protocol_id)
    
    # Generate PDF
    pdf_path = generate_report_pdf(protocol)
    
    # Queue email asynchronously - NON-BLOCKING!
    send_report_ready_notification(protocol, report_pdf_path=pdf_path)
    
    messages.success(request, 'Report sent and email queued!')
    return redirect('protocol_detail', protocol_id=protocol_id)
    # View returns immediately, email queued for background processing
```

## Business Logic

### Automatic Email Triggers

**1. Sample Reception (Step 04)**
```python
# protocols/views.py
def receive_sample_view(request, protocol_id):
    protocol = get_object_or_404(Protocol, id=protocol_id)
    
    # ... receive sample logic ...
    protocol.status = Protocol.Status.RECEIVED
    protocol.reception_date = timezone.now()
    protocol.save()
    
    # Trigger email notification
    send_sample_reception_notification(protocol)
    
    return redirect('protocol_detail', protocol_id=protocol_id)
```

**2. Report Ready (Step 06)**
```python
# protocols/views.py
def send_report_view(request, protocol_id):
    protocol = get_object_or_404(Protocol, id=protocol_id)
    report = protocol.report
    
    # Generate PDF
    pdf_path = generate_report_pdf(protocol, report)
    
    # Update status
    report.sent_at = timezone.now()
    report.save()
    
    # Trigger email notification with attachment
    send_report_ready_notification(protocol, report_pdf_path=pdf_path)
    
    return redirect('protocol_detail', protocol_id=protocol_id)
```

**3. Work Order (Step 07)**
```python
# protocols/views.py
def workorder_send_view(request, order_id):
    work_order = get_object_or_404(WorkOrder, id=order_id)
    
    # Generate PDF
    pdf_path = generate_workorder_pdf(work_order)
    
    # Update status
    work_order.status = WorkOrder.Status.SENT
    work_order.sent_at = timezone.now()
    work_order.save()
    
    # Trigger email notification
    send_work_order_notification(work_order, pdf_path=pdf_path)
    
    return redirect('workorder_detail', order_id=order_id)
```

### Celery Retry Logic (Automatic)

Celery handles retries automatically based on task decorator:

```python
@shared_task(
    max_retries=3,  # Max 3 attempts
    default_retry_delay=60,  # Start with 1 minute
    retry_backoff=True,  # Exponential: 1min, 2min, 4min
    retry_backoff_max=600,  # Max delay 10 minutes
    retry_jitter=True,  # Add randomness
)
```

**Retry Schedule:**
- Attempt 1: Immediate
- Attempt 2: After ~1 minute (+ jitter)
- Attempt 3: After ~2 minutes (+ jitter)
- Attempt 4: After ~4 minutes (+ jitter)
- If all fail: Task marked as FAILURE

### Notification Preferences

```python
# Check preferences before sending
def send_sample_reception_notification(protocol):
    veterinarian = protocol.veterinarian
    
    # Get or create preferences
    prefs, created = NotificationPreference.objects.get_or_create(
        veterinarian=veterinarian
    )
    
    # Check if this type is enabled
    if not prefs.should_send('sample_reception'):
        return None  # Don't send
    
    # Get recipient email (alternative or default)
    recipient_email = prefs.get_recipient_email()
    
    # Queue email
    return queue_email(...)
```

### Email Templates

**Django Template Example:**

```html
<!-- templates/emails/sample_reception.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Muestra Recibida</title>
</head>
<body>
    <h2>Muestra Recibida</h2>
    
    <p>Estimado/a Dr./Dra. {{ veterinarian.user.last_name }},</p>
    
    <p>Confirmamos la recepción de la muestra correspondiente a:</p>
    
    <ul>
        <li><strong>Número de Protocolo:</strong> {{ protocol.protocol_number }}</li>
        <li><strong>Animal:</strong> {{ protocol.animal_identification }} ({{ protocol.species }})</li>
        <li><strong>Fecha de recepción:</strong> {{ protocol.reception_date|date:"d/m/Y" }}</li>
    </ul>
    
    <p>Puede consultar el estado de su protocolo en el portal.</p>
    
    <p>Saludos cordiales,<br>
    Laboratorio de Anatomía Patológica Veterinaria<br>
    Universidad Nacional del Litoral</p>
</body>
</html>
```

```html
<!-- templates/emails/report_ready.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Informe Disponible</title>
</head>
<body>
    <h2>Informe Histopatológico Disponible</h2>
    
    <p>Estimado/a Dr./Dra. {{ veterinarian.user.last_name }},</p>
    
    <p>El informe histopatológico de su protocolo <strong>{{ protocol.protocol_number }}</strong> está disponible.</p>
    
    <ul>
        <li><strong>Protocolo:</strong> {{ protocol.protocol_number }}</li>
        <li><strong>Animal:</strong> {{ protocol.animal_identification }} ({{ protocol.species }})</li>
        <li><strong>Diagnóstico:</strong> {{ report.diagnosis }}</li>
        <li><strong>Histopatólogo:</strong> {{ report.histopathologist.user.get_full_name }}</li>
    </ul>
    
    <p>El informe se encuentra adjunto en formato PDF.</p>
    
    <p>Para cualquier consulta, no dude en contactarnos.</p>
    
    <p>Saludos cordiales,<br>
    {{ report.histopathologist.user.get_full_name }}<br>
    Laboratorio de Anatomía Patológica Veterinaria</p>
</body>
</html>
```

## Acceptance Criteria

1. [ ] Redis installed and configured as Celery broker
2. [ ] Celery workers running and processing tasks
3. [ ] `send_email` Celery task works with all email types
4. [ ] EmailLog model tracks all sent emails
5. [ ] NotificationPreference model allows per-vet settings
6. [ ] Automatic retry on failure (3 attempts, exponential backoff)
7. [ ] Email verification refactored to use queue
8. [ ] Password reset refactored to use queue
9. [ ] Sample reception triggers email notification
10. [ ] Report ready triggers email with PDF attachment
11. [ ] Work order triggers email notification
12. [ ] Email templates render correctly
13. [ ] Notification preferences are respected
14. [ ] Alternative email addresses work
15. [ ] Celery task status tracked in Redis
16. [ ] EmailLog admin interface accessible
17. [ ] Failed tasks visible in Celery Flower
18. [ ] View responses are non-blocking (immediate return)

## Testing Approach

### Unit Tests

**Model Tests:**
- `EmailLog` creation and status updates
- `NotificationPreference` creation and methods
- `get_recipient_email()` returns correct email
- `should_send()` checks preferences correctly

**Email Function Tests:**
- `queue_email()` creates EmailLog
- `queue_email()` dispatches Celery task
- `send_verification_email()` creates correct context
- `send_sample_reception_notification()` checks preferences
- `send_report_ready_notification()` includes attachment

**Template Tests:**
- Email templates render without errors
- Context variables work correctly
- HTML formatting is valid

### Integration Tests

**Celery Task Tests:**
- `send_email.delay()` queues task in Redis
- Task executes and sends email
- EmailLog status updated to SENT on success
- EmailLog status updated to FAILED on error
- Task retries on failure (mock SMTP errors)
- Exponential backoff works correctly

**Email Sending Tests:**
```python
from django.test import TestCase
from unittest.mock import patch
from protocols.tasks import send_email
from protocols.models import EmailLog

class EmailTaskTest(TestCase):
    @patch('protocols.tasks.EmailMultiAlternatives.send')
    def test_send_email_success(self, mock_send):
        """Test successful email sending."""
        # Create EmailLog
        email_log = EmailLog.objects.create(
            email_type='sample_reception',
            recipient_email='test@example.com',
            subject='Test',
            celery_task_id='test-task-id',
        )
        
        # Call task synchronously (for testing)
        result = send_email(
            email_type='sample_reception',
            recipient_email='test@example.com',
            subject='Test Subject',
            context={'protocol': mock_protocol},
            email_log_id=email_log.id
        )
        
        # Assert
        self.assertTrue(result['success'])
        mock_send.assert_called_once()
        
        # Check EmailLog updated
        email_log.refresh_from_db()
        self.assertEqual(email_log.status, EmailLog.Status.SENT)
        self.assertIsNotNone(email_log.sent_at)
```

**Preference Tests:**
- Disabled notification types are not sent
- Alternative email is used when set
- Attachments excluded when preference set

### E2E Tests

**Full Flow Tests:**
```python
def test_sample_reception_email_flow(self):
    """Test complete flow from sample reception to email sent."""
    # Setup
    veterinarian = create_veterinarian()
    protocol = create_protocol(veterinarian=veterinarian)
    
    # Trigger
    receive_sample(protocol)
    
    # Assert task queued
    from protocols.models import EmailLog
    email_log = EmailLog.objects.filter(
        protocol=protocol,
        email_type='sample_reception'
    ).first()
    
    self.assertIsNotNone(email_log)
    self.assertEqual(email_log.status, EmailLog.Status.QUEUED)
    
    # Run Celery task (synchronously for test)
    task = send_email.apply_async(...)
    task.get()  # Wait for completion
    
    # Assert email sent
    email_log.refresh_from_db()
    self.assertEqual(email_log.status, EmailLog.Status.SENT)
```

### Celery Monitoring Tests

- View Celery Flower dashboard
- Check task success/failure rates
- Monitor queue length
- Check worker status
- Verify retry attempts in Flower

## Technical Considerations

### Infrastructure Setup

**Docker Compose Setup**

The project includes Redis, Celery, and Flower services in `compose.yaml`:

```bash
# Start Redis
docker compose --profile redis up -d

# Start Celery worker
docker compose --profile worker up -d

# Start Celery beat (for scheduled tasks)
docker compose --profile beat up -d

# Start Flower monitoring
docker compose --profile flower up -d

# Access Flower at http://localhost:5555
```

### Email Service Configuration

**SMTP Settings (Django):**
```python
# settings.py

# Email backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# SMTP configuration
EMAIL_HOST = env('EMAIL_HOST', default='smtp.unl.edu.ar')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

# From email
DEFAULT_FROM_EMAIL = 'Laboratorio AP <lab@veterinaria.unl.edu.ar>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
```

**Alternative: Using Gmail (Development)**
```python
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'  # Not regular password!
EMAIL_USE_TLS = True
```

### Performance Optimization

**Celery Concurrency:**
```bash
# Multiple workers
celery -A config worker -l INFO --concurrency=4

# Or auto-detect CPUs
celery -A config worker -l INFO --concurrency=0
```

**Task Routing (Optional):**
```python
# settings.py
CELERY_TASK_ROUTES = {
    'protocols.tasks.send_email': {'queue': 'emails'},
    'protocols.tasks.generate_report': {'queue': 'reports'},
}

# Run separate workers per queue
celery -A config worker -Q emails -l INFO
celery -A config worker -Q reports -l INFO
```

**Redis Connection Pool:**
```python
# settings.py
CELERY_BROKER_POOL_LIMIT = 10
CELERY_BROKER_CONNECTION_MAX_RETRIES = 5
```

### Security & Privacy

**TLS for SMTP:**
```python
EMAIL_USE_TLS = True  # Always use TLS
EMAIL_SSL_CERTFILE = None  # Optional: custom cert
EMAIL_SSL_KEYFILE = None
```

**Sensitive Data Handling:**
- ✅ Don't include full medical data in email body
- ✅ Use generic descriptions in subject lines
- ✅ Sensitive info only in password-protected PDF attachments
- ✅ Respect veterinarian notification preferences
- ✅ Allow alternative email addresses

**Redis Security:**
```bash
# /etc/redis/redis.conf
requirepass your_redis_password
bind 127.0.0.1  # Only localhost
```

```python
# settings.py
REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
```

### Monitoring & Debugging

**Celery Flower:**
- Real-time task monitoring
- Task history and statistics
- Worker status and performance
- Task retry visualization
- Manual task retries

**Logging:**
```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'celery': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/celery.log',
        },
    },
    'loggers': {
        'celery': {
            'handlers': ['celery'],
            'level': 'INFO',
        },
    },
}
```

**Redis Monitoring:**
```bash
# Redis CLI via Docker
docker compose exec redis redis-cli
> INFO stats
> LLEN celery  # Check queue length
```

## Dependencies

### Infrastructure:
- **Docker Compose**: For running Redis, Celery, and Flower services
- **Redis**: Message broker (included in docker-compose)
- **Celery**: Task queue (included in docker-compose)
- **Flower**: Monitoring dashboard (included in docker-compose)

### Django Apps:
- Step 01: Authentication (User model)
- Step 02: Veterinarian Profiles (for email addresses)

### Will be used by:
- Step 01: Email verification (refactor)
- Step 04: Sample Reception (notification)
- Step 06: Report Generation (notification with PDF)
- Step 07: Work Orders (notification with PDF)
- Step 12: System Admin (custom notifications)

### Docker Services:
```yaml
# Already configured in compose.yaml
redis:     # Message broker
worker:    # Celery worker
beat:      # Celery beat (scheduled tasks)
flower:    # Monitoring dashboard
```

## Estimated Effort

**Time**: 3-4 days

**Breakdown**:
- Redis + Celery setup: 0.5 day
- EmailLog and NotificationPreference models: 0.5 day
- `send_email` Celery task: 0.5 day
- Email helper functions: 0.5 day
- Email templates (5 templates): 0.5 day
- Refactor existing email code: 0.5 day
- Testing: 1 day
- Documentation: 0.5 day

**Note**: Most complexity handled by Celery. Much simpler than custom queue implementation!

## Implementation Notes

### File Structure

```
laboratory-system/
├── src/
│   ├── config/
│   │   ├── celery.py              # Celery app configuration
│   │   └── settings.py            # Redis + email settings
│   │
│   ├── protocols/
│   │   ├── models.py              # EmailLog, NotificationPreference
│   │   ├── tasks.py               # send_email Celery task
│   │   ├── emails.py              # Helper functions
│   │   └── admin.py               # EmailLog admin
│   │
│   └── templates/
│       └── emails/
│           ├── verification.html
│           ├── password_reset.html
│           ├── sample_reception.html
│           ├── report_ready.html
│           └── work_order.html
```

### Quick Start Guide

**1. Start Redis and Celery services:**
```bash
# Start all required services
docker compose --profile redis --profile worker --profile flower up -d

# Or start individually
docker compose --profile redis up -d
docker compose --profile worker up -d
docker compose --profile flower up -d
```

**2. Access Flower monitoring:**
```bash
# Open http://localhost:5555 in your browser
```

**3. Configure Django settings:**
```python
# settings.py
CELERY_BROKER_URL = 'redis://redis:6379/0'  # Note: 'redis' is the service name
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.unl.edu.ar'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

**4. Create config/celery.py:**
```python
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('laboratory')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

**5. Update config/__init__.py:**
```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### Usage Examples

**Send Email Verification:**
```python
from protocols.emails import send_verification_email

# In registration view
user = User.objects.create_user(...)
send_verification_email(user)  # Returns EmailLog, queues task
```

**Send Sample Reception Notification:**
```python
from protocols.emails import send_sample_reception_notification

# In sample reception view
protocol.status = Protocol.Status.RECEIVED
protocol.save()
send_sample_reception_notification(protocol)
```

**Send Report Ready with PDF:**
```python
from protocols.emails import send_report_ready_notification

# In report sending view
pdf_path = generate_report_pdf(protocol)
send_report_ready_notification(protocol, report_pdf_path=pdf_path)
```

### Monitoring

**Docker Compose Services:**
```bash
# Check service status
docker compose ps

# View logs
docker compose logs worker
docker compose logs flower
docker compose logs redis

# Restart services
docker compose restart worker
docker compose restart flower
```

**Check Celery Worker Status:**
```bash
# Check active tasks
docker compose exec worker celery -A config inspect active

# Check worker statistics
docker compose exec worker celery -A config inspect stats
```

**View Task Results:**
```bash
# View specific task result
docker compose exec worker celery -A config result <task-id>
```

**Monitor in Flower:**
- Open http://localhost:5555
- View active tasks
- Check task history
- Monitor worker health
- Retry failed tasks
- Real-time task monitoring
- Worker statistics

### Docker Compose Environment Variables

Add these to your `.env` file for Docker Compose configuration:

```bash
# Celery Configuration
CELERY_LOG_LEVEL=info
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email Configuration
EMAIL_HOST=smtp.unl.edu.ar
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your_email@unl.edu.ar
EMAIL_HOST_PASSWORD=your_password
DEFAULT_FROM_EMAIL=Laboratorio AP <lab@veterinaria.unl.edu.ar>

# Docker Resource Limits (optional)
DOCKER_REDIS_CPUS=0.5
DOCKER_REDIS_MEMORY=512m
DOCKER_WORKER_CPUS=1
DOCKER_WORKER_MEMORY=1g
DOCKER_FLOWER_CPUS=0.25
DOCKER_FLOWER_MEMORY=256m

# Port Forwarding
DOCKER_FLOWER_PORT_FORWARD=127.0.0.1:5555
```

### Production Deployment

**Docker Compose Production:**

```bash
# Production deployment
docker compose --profile redis --profile worker --profile flower --profile web up -d

# Scale workers if needed
docker compose up -d --scale worker=3
```

### Testing Checklist

**Docker Compose Setup:**
- [ ] Redis service starts: `docker compose --profile redis up -d`
- [ ] Celery worker starts: `docker compose --profile worker up -d`
- [ ] Flower starts: `docker compose --profile flower up -d`
- [ ] Flower accessible at http://localhost:5555
- [ ] All services show as "Up" in `docker compose ps`

**Email Functionality:**
- [ ] Sample reception triggers email
- [ ] Report sent triggers email with PDF
- [ ] Work order triggers email
- [ ] Email verification refactored
- [ ] Password reset refactored
- [ ] Templates render correctly
- [ ] Notification preferences work
- [ ] Alternative emails work
- [ ] Attachments included correctly
- [ ] Failed sends retry automatically
- [ ] EmailLog tracks all emails
- [ ] Celery Flower shows tasks
- [ ] Views return immediately (non-blocking)

**Docker Compose Testing:**
- [ ] `docker compose logs worker` shows no errors
- [ ] `docker compose logs flower` shows no errors
- [ ] `docker compose exec worker celery -A config inspect active` works
- [ ] Tasks appear in Flower dashboard
- [ ] Email tasks complete successfully

### Refactoring Checklist

Existing code to refactor:
- [ ] Email verification in Step 01
- [ ] Password reset in Step 01
- [ ] Any manual `send_mail()` calls
- [ ] Replace synchronous with async `.delay()` calls
- [ ] Add EmailLog tracking
- [ ] Check notification preferences

