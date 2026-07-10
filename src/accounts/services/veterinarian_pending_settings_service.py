"""
Veterinarian pending-approval screen: Markdown rendering and Redis cache.
"""

from django.core.cache import cache

from accounts.models import VeterinarianPendingApprovalSettings
from pages.services.dashboard_announcement_service import render_message_safe

CACHE_KEY = "veterinarian_pending_approval:settings"
CACHE_TIMEOUT = 86400


def invalidate_pending_settings_cache() -> None:
    """Remove cached pending-approval screen payload after admin update."""
    cache.delete(CACHE_KEY)


def _payload_from_instance(
    obj: VeterinarianPendingApprovalSettings,
) -> dict:
    """Build template payload from a DB row."""
    message_html = ""
    if obj.message.strip():
        message_html = render_message_safe(obj.message)

    return {
        "is_active": obj.is_active,
        "title": obj.title,
        "message_html": message_html,
        "contact_phone": obj.contact_phone,
        "contact_email": obj.contact_email,
        "updated_at": obj.updated_at.isoformat(),
    }


def get_cached_pending_settings() -> dict:
    """
    Return pending-approval screen context from cache or DB.

    Returns:
        dict: Screen content for template rendering
    """
    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return cached

    obj = VeterinarianPendingApprovalSettings.objects.filter(
        pk=VeterinarianPendingApprovalSettings.SINGLETON_PK
    ).first()
    if obj is None:
        payload = _default_payload()
        cache.set(CACHE_KEY, payload, CACHE_TIMEOUT)
        return payload

    payload = _payload_from_instance(obj)
    cache.set(CACHE_KEY, payload, CACHE_TIMEOUT)
    return payload


def warm_pending_settings_cache() -> dict:
    """
    Rebuild cache after admin save.

    Returns:
        dict: Fresh cached payload
    """
    invalidate_pending_settings_cache()
    return get_cached_pending_settings()


def _default_payload() -> dict:
    """Return fallback content when no singleton exists yet."""
    return {
        "is_active": True,
        "title": "Cuenta pendiente de habilitación",
        "message_html": "",
        "contact_phone": "",
        "contact_email": "",
        "updated_at": "",
    }
