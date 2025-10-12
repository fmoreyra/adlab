"""
Celery tasks for the protocols app.
Handles asynchronous email sending with retry logic.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from protocols.models import EmailLog, Protocol, WorkOrder

logger = logging.getLogger(__name__)


def _deserialize_context_for_templates(context):
    """
    Deserialize context for templates by reconstructing Django model instances.

    Args:
        context: Serialized context dict from Celery

    Returns:
        dict: Context with reconstructed model instances for templates
    """
    deserialized_context = {}

    for key, value in context.items():
        if (
            isinstance(value, list)
            and value
            and isinstance(value[0], dict)
            and "id" in value[0]
            and "model" in value[0]
        ):
            # Reconstruct QuerySet from list of serialized objects
            model_instances = []
            for item in value:
                model_name = item["model"]
                model_id = item["id"]

                try:
                    if model_name == "Protocol":
                        model_instance = Protocol.objects.get(id=model_id)
                    elif model_name == "WorkOrder":
                        model_instance = WorkOrder.objects.get(id=model_id)
                    else:
                        # For other models, just use the string representation
                        model_instance = item["str"]

                    model_instances.append(model_instance)
                except Exception as e:
                    logger.warning(
                        f"Could not reconstruct {model_name} with id {model_id}: {e}"
                    )
                    # Fallback to string representation
                    model_instances.append(item["str"])

            deserialized_context[key] = model_instances
        elif isinstance(value, dict) and "id" in value and "model" in value:
            # Reconstruct model instance
            model_name = value["model"]
            model_id = value["id"]

            try:
                if model_name == "Protocol":
                    model_instance = Protocol.objects.get(id=model_id)
                elif model_name == "WorkOrder":
                    model_instance = WorkOrder.objects.get(id=model_id)
                else:
                    # For other models, just use the string representation
                    model_instance = value["str"]

                deserialized_context[key] = model_instance
            except Exception as e:
                logger.warning(
                    f"Could not reconstruct {model_name} with id {model_id}: {e}"
                )
                # Fallback to string representation
                deserialized_context[key] = value["str"]
        elif isinstance(value, dict):
            # Recursively deserialize nested dicts
            deserialized_context[key] = _deserialize_context_for_templates(
                value
            )
        else:
            # Keep primitive types as-is
            deserialized_context[key] = value

    return deserialized_context


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
    email_log_id=None,
):
    """
    Unified email sending task with automatic retry.

    Args:
        email_type: Type of email (from EmailLog.EmailType)
        recipient_email: Recipient email address
        subject: Email subject
        context: Template context dict
        template_name: Optional custom template (defaults based on email_type)
        attachment_path: Optional path to PDF attachment
        email_log_id: Optional EmailLog ID for tracking

    Returns:
        dict: {'success': bool, 'message': str, 'task_id': str}

    Raises:
        Exception: Re-raises exceptions for Celery retry mechanism
    """
    try:
        # Determine template
        if not template_name:
            template_map = {
                "email_verification": "emails/email_verification.html",
                "password_reset": "emails/password_reset.html",
                "sample_reception": "emails/sample_reception.html",
                "report_ready": "emails/report_ready.html",
                "work_order": "emails/work_order.html",
            }
            template_name = template_map.get(email_type, "emails/default.html")

        # Deserialize context for templates
        template_context = _deserialize_context_for_templates(context)

        # Render email HTML
        html_content = render_to_string(template_name, template_context)
        plain_content = strip_tags(html_content)

        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_content,  # Plain text fallback
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
                email_log.save(update_fields=["status", "sent_at"])
            except EmailLog.DoesNotExist:
                logger.warning(f"EmailLog {email_log_id} not found")

        logger.info(f"Email sent: {email_type} to {recipient_email}")

        return {
            "success": True,
            "message": f"Email sent to {recipient_email}",
            "task_id": self.request.id,
        }

    except Exception as exc:
        # Update EmailLog with error
        if email_log_id:
            try:
                email_log = EmailLog.objects.get(id=email_log_id)
                email_log.status = EmailLog.Status.FAILED
                email_log.error_message = str(exc)
                email_log.save(update_fields=["status", "error_message"])
            except EmailLog.DoesNotExist:
                logger.warning(f"EmailLog {email_log_id} not found")

        logger.error(
            f"Email failed: {email_type} to {recipient_email} - {exc}"
        )

        # Re-raise for Celery retry
        raise
