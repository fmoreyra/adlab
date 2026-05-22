"""
Dashboard announcement banner: Markdown rendering, sanitization, and cache.
"""

import re

import bleach
import markdown
from django.core.cache import cache

from pages.models import DashboardAnnouncement

CACHE_KEY = "dashboard_announcement:active"
CACHE_TIMEOUT = 86400  # 24h safety net; invalidation on save is primary

ALLOWED_TAGS = ["p", "strong", "em", "a", "ul", "ol", "li", "br"]
ALLOWED_ATTRIBUTES = {"a": ["href", "rel", "target"]}


def render_message_safe(markdown_text: str) -> str:
    """
    Convert Markdown to sanitized HTML safe for template rendering.

    Args:
        markdown_text: Raw Markdown from the admin form

    Returns:
        str: Bleach-sanitized HTML fragment
    """
    if not markdown_text or not markdown_text.strip():
        return ""
    html = markdown.markdown(
        markdown_text,
        extensions=["nl2br", "sane_lists"],
    )
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )
    return bleach.linkify(
        cleaned,
        callbacks=[bleach.callbacks.nofollow],
        parse_email=False,
    )


def _plain_text_from_markdown(
    markdown_text: str, max_length: int = 200
) -> str:
    """Strip Markdown to plain text for notification body previews."""
    text = markdown_text or ""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_#>`]", "", text)
    text = " ".join(text.split())
    if len(text) > max_length:
        return f"{text[: max_length - 3]}..."
    return text


def invalidate_banner_cache() -> None:
    """Remove cached banner payload after admin update."""
    cache.delete(CACHE_KEY)


def _payload_from_instance(obj: DashboardAnnouncement) -> dict | None:
    """Build cache/template payload from a DB row."""
    if not obj.is_active or not obj.message.strip():
        return None
    return {
        "is_active": True,
        "html": render_message_safe(obj.message),
        "updated_at": obj.updated_at.isoformat(),
    }


def get_cached_banner() -> dict | None:
    """
    Return banner context from cache or DB, populating cache on miss.

    Returns:
        dict with keys html, updated_at, is_active; or None if inactive/empty
    """
    cached = cache.get(CACHE_KEY)
    if cached is not None:
        if cached == {}:
            return None
        return cached

    obj = DashboardAnnouncement.objects.filter(
        pk=DashboardAnnouncement.SINGLETON_PK
    ).first()
    if obj is None:
        cache.set(CACHE_KEY, {}, CACHE_TIMEOUT)
        return None

    payload = _payload_from_instance(obj)
    cache.set(CACHE_KEY, payload if payload is not None else {}, CACHE_TIMEOUT)
    return payload


def warm_banner_cache() -> dict | None:
    """
    Rebuild cache after save (optional warming).

    Returns:
        dict | None: Same as get_cached_banner after repopulating cache
    """
    invalidate_banner_cache()
    return get_cached_banner()


def get_notification_preview_body(markdown_text: str) -> str:
    """
    Plain-text excerpt for in-app notification body.

    Args:
        markdown_text: Source Markdown message

    Returns:
        str: Truncated plain text
    """
    return _plain_text_from_markdown(markdown_text)
