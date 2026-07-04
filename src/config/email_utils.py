"""
Shared email helpers: recipient override and daily send metrics.
"""

from datetime import date, datetime, time, timedelta
from typing import Optional

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

# Substrings in SMTP error messages that indicate Gmail daily quota exceeded.
_SMTP_QUOTA_ERROR_MARKERS = (
    "5.4.5",
    "daily user sending limit",
    "limit for sending mail",
    "reached a limit for sending",
    "you have reached a limit for sending",
)


def get_email_recipient_override() -> str:
    """
    Return configured recipient override, or empty string if unset.

    Returns:
        str: Override address when EMAIL_RECIPIENT_OVERRIDE is set
    """
    return (getattr(settings, "EMAIL_RECIPIENT_OVERRIDE", None) or "").strip()


def resolve_recipient_email(intended_email: str) -> str:
    """
    Resolve the delivery address for an outbound email.

    When EMAIL_RECIPIENT_OVERRIDE is set, all mail goes there (local/dev).
    When unset, the intended recipient is used unchanged.

    Args:
        intended_email: Logical recipient (user/veterinarian address)

    Returns:
        str: Address to pass to the mail backend
    """
    override = get_email_recipient_override()
    if override:
        return override
    return intended_email


def annotate_subject_for_override(subject: str, intended_email: str) -> str:
    """
    Prefix subject with the intended recipient when override is active.

    Args:
        subject: Original subject line
        intended_email: Logical recipient before override

    Returns:
        str: Subject, possibly annotated for debugging
    """
    override = get_email_recipient_override()
    if not override:
        return subject
    if override.lower() == (intended_email or "").lower():
        return subject
    return f"[para: {intended_email}] {subject}"


def apply_recipient_override(
    intended_email: str, subject: str
) -> tuple[str, str]:
    """
    Apply recipient override and subject annotation together.

    Args:
        intended_email: Logical recipient
        subject: Original subject

    Returns:
        tuple[str, str]: (delivery_email, subject_for_send)
    """
    delivery = resolve_recipient_email(intended_email)
    annotated = annotate_subject_for_override(subject, intended_email)
    return delivery, annotated


def is_smtp_quota_error(error_message: str) -> bool:
    """
    Return True when an SMTP error likely indicates a daily send quota hit.

    Gmail typically returns codes like ``550 5.4.5 Daily user sending limit``.

    Args:
        error_message: Error text stored on EmailLog or raised by the backend

    Returns:
        bool: True when the message matches known quota patterns
    """
    if not error_message:
        return False
    lowered = error_message.lower()
    return any(marker in lowered for marker in _SMTP_QUOTA_ERROR_MARKERS)


def _get_email_daily_limit() -> int:
    """Return configured soft daily budget for admin metrics."""
    return int(getattr(settings, "EMAIL_DAILY_LIMIT", 500) or 500)


def count_emails_sent_rolling_24h(
    reference_time: Optional[datetime] = None,
) -> dict:
    """
    Count EmailLog messages in the last 24 hours (Gmail-style rolling window).

    Args:
        reference_time: End of the window; defaults to now in the active TZ

    Returns:
        dict: window_end, sent, failed, queued, limit, remaining
    """
    from protocols.models import EmailLog

    window_end = reference_time or timezone.now()
    window_start = window_end - timedelta(hours=24)
    limit = _get_email_daily_limit()

    sent_count = EmailLog.objects.filter(
        status=EmailLog.Status.SENT,
        sent_at__gte=window_start,
        sent_at__lte=window_end,
    ).count()
    failed = EmailLog.objects.filter(
        status=EmailLog.Status.FAILED,
        created_at__gte=window_start,
        created_at__lte=window_end,
    ).count()
    queued = EmailLog.objects.filter(
        status=EmailLog.Status.QUEUED,
        created_at__gte=window_start,
        created_at__lte=window_end,
    ).count()
    quota_query = Q()
    for marker in _SMTP_QUOTA_ERROR_MARKERS:
        quota_query |= Q(error_message__icontains=marker)
    quota_failures = (
        EmailLog.objects.filter(
            status=EmailLog.Status.FAILED,
            created_at__gte=window_start,
            created_at__lte=window_end,
        )
        .filter(quota_query)
        .count()
    )

    return {
        "window_start": window_start,
        "window_end": window_end,
        "sent": sent_count,
        "failed": failed,
        "queued": queued,
        "quota_failures": quota_failures,
        "limit": limit,
        "remaining": max(0, limit - sent_count),
    }


def count_emails_sent_on(day: Optional[date] = None) -> dict:
    """
    Count EmailLog messages for a calendar day (local timezone).

    Useful for day-by-day history. Gmail applies a rolling 24-hour quota;
    see ``count_emails_sent_rolling_24h`` for a closer approximation.

    Args:
        day: Day to measure; defaults to today in the active timezone

    Returns:
        dict: day, sent, failed, queued, limit, remaining
    """
    from protocols.models import EmailLog

    day = day or timezone.localdate()
    start = timezone.make_aware(datetime.combine(day, time.min))
    end = timezone.make_aware(datetime.combine(day, time.max))

    sent_count = EmailLog.objects.filter(
        status=EmailLog.Status.SENT,
        sent_at__gte=start,
        sent_at__lte=end,
    ).count()
    failed = EmailLog.objects.filter(
        status=EmailLog.Status.FAILED,
        created_at__gte=start,
        created_at__lte=end,
    ).count()
    queued = EmailLog.objects.filter(
        status=EmailLog.Status.QUEUED,
        created_at__gte=start,
        created_at__lte=end,
    ).count()
    limit = _get_email_daily_limit()

    return {
        "day": day,
        "sent": sent_count,
        "failed": failed,
        "queued": queued,
        "limit": limit,
        "remaining": max(0, limit - sent_count),
    }


def build_email_quota_metrics(day: Optional[date] = None) -> dict:
    """
    Build calendar-day and rolling-24h send metrics for the admin UI.

    Args:
        day: Calendar day for the historical counter

    Returns:
        dict: calendar, rolling_24h
    """
    return {
        "calendar": count_emails_sent_on(day),
        "rolling_24h": count_emails_sent_rolling_24h(),
    }
