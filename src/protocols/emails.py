"""
Email helper functions for the protocols app.
Provides high-level functions to queue emails via Celery.
"""

import logging

from protocols.models import EmailLog, NotificationPreference
from protocols.tasks import send_email

logger = logging.getLogger(__name__)


def _serialize_context_for_celery(context):
    """
    Serialize context for Celery by converting Django model instances to IDs.

    Args:
        context: Template context dict that may contain Django model instances

    Returns:
        dict: Serialized context safe for Celery JSON serialization
    """
    serialized_context = {}

    for key, value in context.items():
        if hasattr(value, "pk"):  # Django model instance
            # Convert model instance to a dict with basic info
            serialized_context[key] = {
                "id": value.pk,
                "model": value.__class__.__name__,
                "str": str(value),
            }
        elif hasattr(value, "model"):  # Django QuerySet
            # Convert QuerySet to list of serialized objects
            serialized_context[key] = [
                {
                    "id": obj.pk,
                    "model": obj.__class__.__name__,
                    "str": str(obj),
                }
                for obj in value
            ]
        elif isinstance(value, dict):
            # Recursively serialize nested dicts
            serialized_context[key] = _serialize_context_for_celery(value)
        else:
            # Keep primitive types as-is
            serialized_context[key] = value

    return serialized_context


def queue_email(
    email_type,
    recipient_email,
    subject,
    context,
    template_name=None,
    attachment_path=None,
    protocol=None,
    work_order=None,
    veterinarian=None,
):
    """
    Queue an email for sending via Celery.

    Args:
        email_type: EmailLog.EmailType choice
        recipient_email: Recipient email address
        subject: Email subject
        context: Template context dict
        template_name: Optional custom template
        attachment_path: Optional path to PDF attachment
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
        celery_task_id="",  # Will be set after task dispatch
        status=EmailLog.Status.QUEUED,
        has_attachment=bool(attachment_path),
    )

    # Serialize context for Celery
    serialized_context = _serialize_context_for_celery(context)

    # Dispatch Celery task
    task = send_email.delay(
        email_type=email_type,
        recipient_email=recipient_email,
        subject=subject,
        context=serialized_context,
        template_name=template_name,
        attachment_path=attachment_path,
        email_log_id=email_log.id,
    )

    # Update EmailLog with task ID
    email_log.celery_task_id = task.id
    email_log.save(update_fields=["celery_task_id"])

    logger.info(
        f"Email queued: {email_type} to {recipient_email} (task: {task.id})"
    )

    return email_log


def send_verification_email(user, verification_url):
    """
    Send email verification email.

    Args:
        user: User instance
        verification_url: Full URL for email verification

    Returns:
        EmailLog: Created email log instance
    """
    return queue_email(
        email_type=EmailLog.EmailType.EMAIL_VERIFICATION,
        recipient_email=user.email,
        subject="Verifique su correo electrónico - AdLab Veterinario",
        context={
            "user": user,
            "verification_url": verification_url,
        },
    )


def send_password_reset_email(user, reset_url, expiry_hours=1):
    """
    Send password reset email.

    Args:
        user: User instance
        reset_url: Full URL for password reset
        expiry_hours: Hours until reset link expires

    Returns:
        EmailLog: Created email log instance
    """
    return queue_email(
        email_type=EmailLog.EmailType.PASSWORD_RESET,
        recipient_email=user.email,
        subject="Restablezca su contraseña - AdLab Veterinario",
        context={
            "user": user,
            "reset_url": reset_url,
            "expiry_hours": expiry_hours,
        },
    )


def send_sample_reception_notification(protocol):
    """
    Send sample reception notification to veterinarian.

    Args:
        protocol: Protocol instance

    Returns:
        EmailLog or None: Created email log instance, or None if not sent
    """
    veterinarian = protocol.veterinarian

    # Check preferences
    prefs, _ = NotificationPreference.objects.get_or_create(
        veterinarian=veterinarian
    )
    if not prefs.should_send("sample_reception"):
        logger.info(
            f"Sample reception notification skipped for {veterinarian} (preferences)"
        )
        return None

    recipient_email = prefs.get_recipient_email()

    return queue_email(
        email_type=EmailLog.EmailType.SAMPLE_RECEPTION,
        recipient_email=recipient_email,
        subject=f"Muestra recibida - Protocolo {protocol.protocol_number}",
        context={
            "protocol": protocol,
            "veterinarian": veterinarian,
        },
        protocol=protocol,
        veterinarian=veterinarian,
    )


def send_sample_rejection_notification(protocol):
    """
    Send sample rejection notification to veterinarian.

    Args:
        protocol: Protocol instance

    Returns:
        EmailLog or None: Created email log instance, or None if not sent
    """
    veterinarian = protocol.veterinarian

    # Check preferences
    prefs, _ = NotificationPreference.objects.get_or_create(
        veterinarian=veterinarian
    )
    if not prefs.should_send("sample_reception"):  # Use same preference
        logger.info(
            f"Sample rejection notification skipped for {veterinarian} (preferences)"
        )
        return None

    recipient_email = prefs.get_recipient_email()

    return queue_email(
        email_type=EmailLog.EmailType.SAMPLE_RECEPTION,  # Reuse type
        recipient_email=recipient_email,
        subject=f"Muestra rechazada - Protocolo {protocol.protocol_number}",
        context={
            "protocol": protocol,
            "veterinarian": veterinarian,
        },
        protocol=protocol,
        veterinarian=veterinarian,
        template_name="protocols/emails/sample_rejection.html",
    )


def send_report_ready_notification(protocol, report_pdf_path=None):
    """
    Send report ready notification with optional PDF attachment.

    Args:
        protocol: Protocol instance
        report_pdf_path: Optional path to report PDF file

    Returns:
        EmailLog or None: Created email log instance, or None if not sent
    """
    veterinarian = protocol.veterinarian

    # Check preferences
    prefs, _ = NotificationPreference.objects.get_or_create(
        veterinarian=veterinarian
    )
    if not prefs.should_send("report_ready"):
        logger.info(
            f"Report ready notification skipped for {veterinarian} (preferences)"
        )
        return None

    recipient_email = prefs.get_recipient_email()
    attachment = report_pdf_path if prefs.include_attachments else None

    return queue_email(
        email_type=EmailLog.EmailType.REPORT_READY,
        recipient_email=recipient_email,
        subject=f"Informe disponible - Protocolo {protocol.protocol_number}",
        context={
            "protocol": protocol,
            "veterinarian": veterinarian,
            "has_attachment": bool(attachment),
        },
        attachment_path=attachment,
        protocol=protocol,
        veterinarian=veterinarian,
    )


def send_work_order_notification(work_order, work_order_pdf_path=None):
    """
    Send work order notification with optional PDF attachment.

    Args:
        work_order: WorkOrder instance
        work_order_pdf_path: Optional path to work order PDF file

    Returns:
        list: List of EmailLog instances (one per protocol/veterinarian)
    """
    email_logs = []

    # Get unique veterinarians from protocols in this work order
    veterinarians = set()
    for protocol in work_order.protocols.all():
        veterinarians.add(protocol.veterinarian)

    for veterinarian in veterinarians:
        # Check preferences
        prefs, _ = NotificationPreference.objects.get_or_create(
            veterinarian=veterinarian
        )

        recipient_email = prefs.get_recipient_email()
        attachment = work_order_pdf_path if prefs.include_attachments else None

        # Get veterinarian's protocols in this work order
        vet_protocols = work_order.protocols.filter(veterinarian=veterinarian)

        email_log = queue_email(
            email_type=EmailLog.EmailType.WORK_ORDER,
            recipient_email=recipient_email,
            subject=f"Orden de trabajo - {work_order.order_number}",
            context={
                "work_order": work_order,
                "veterinarian": veterinarian,
                "protocols": vet_protocols,
                "has_attachment": bool(attachment),
            },
            attachment_path=attachment,
            work_order=work_order,
            veterinarian=veterinarian,
        )
        email_logs.append(email_log)

    return email_logs


def send_custom_notification(
    recipient_email, subject, context, template_name, veterinarian=None
):
    """
    Send custom notification email.

    Args:
        recipient_email: Recipient email address
        subject: Email subject
        context: Template context dict
        template_name: Template file name
        veterinarian: Optional Veterinarian instance

    Returns:
        EmailLog: Created email log instance
    """
    return queue_email(
        email_type=EmailLog.EmailType.CUSTOM,
        recipient_email=recipient_email,
        subject=subject,
        context=context,
        template_name=template_name,
        veterinarian=veterinarian,
    )
