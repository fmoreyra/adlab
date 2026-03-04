"""
Celery tasks for the protocols app.
Handles asynchronous email sending with retry logic and optional monitoring alerts.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
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


_CONTAINER_ALERT_CACHE_KEY = "container_memory_alert_cooldown"


@shared_task
def check_container_memory_alerts():
    """
    Periodic task: check Docker container memory usage and email admins if any
    container is above CONTAINER_MEMORY_ALERT_THRESHOLD. Uses a cooldown so
    the same alert is not sent more than once per CONTAINER_MEMORY_ALERT_COOLDOWN_SECONDS.
    """
    from django.contrib.auth import get_user_model
    from django.core.cache import cache

    User = get_user_model()
    threshold = getattr(settings, "CONTAINER_MEMORY_ALERT_THRESHOLD", 85)
    name_filter = getattr(
        settings, "CONTAINER_MEMORY_ALERT_NAME_FILTER", "laboratory-web"
    )
    cooldown_seconds = getattr(
        settings, "CONTAINER_MEMORY_ALERT_COOLDOWN_SECONDS", 3600
    )

    if threshold <= 0:
        return

    if cache.get(_CONTAINER_ALERT_CACHE_KEY):
        logger.debug("Container memory alert skipped (cooldown active)")
        return

    try:
        from services.server_stats_service import get_docker_stats
    except ImportError:
        logger.debug("Docker stats not available, skipping container alert")
        return

    data = get_docker_stats()
    if data.get("error"):
        logger.warning("Container memory check failed: %s", data["error"])
        return

    over = []
    for c in data.get("containers") or []:
        name = c.get("name") or ""
        if name_filter and name_filter not in name:
            continue
        pct = c.get("memory_percent")
        if pct is not None and pct >= threshold:
            over.append(
                {
                    "name": name,
                    "memory_percent": pct,
                    "memory_usage_bytes": c.get("memory_usage_bytes"),
                    "memory_limit_bytes": c.get("memory_limit_bytes"),
                }
            )

    if not over:
        return

    admin_emails = list(
        User.objects.filter(
            Q(role=User.Role.ADMIN) | Q(is_superuser=True),
            is_active=True,
        )
        .exclude(email="")
        .values_list("email", flat=True)
        .distinct()
    )
    if not admin_emails:
        logger.warning("No admin emails for container memory alert")
        return

    lines = [
        "Los siguientes contenedores superan el umbral de memoria configurado (%s%%):",
        "",
    ]
    for item in over:
        lines.append("  - %s: %.1f%%" % (item["name"], item["memory_percent"]))
    lines.extend(
        [
            "",
            "Revisa el panel de administración del servidor o considera aumentar el límite de memoria del contenedor.",
        ]
    )
    body = "\n".join(lines) % threshold

    try:
        email = EmailMultiAlternatives(
            subject="[AdLab] Alerta: uso alto de memoria en contenedores",
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=admin_emails,
        )
        email.send(fail_silently=False)
        cache.set(_CONTAINER_ALERT_CACHE_KEY, "1", cooldown_seconds)
        logger.info(
            "Container memory alert sent to %s admins for %s",
            len(admin_emails),
            [x["name"] for x in over],
        )
    except Exception as e:
        logger.exception("Failed to send container memory alert: %s", e)
