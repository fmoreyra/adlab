"""Helpers for in-app notification links and redirects."""

from urllib.parse import urlparse

from django.urls import reverse


def resolve_notification_destination(link_url: str) -> str:
    """
    Normalize stored notification link to a same-site path.

    Supports legacy absolute URLs (any host) and relative paths.

    Args:
        link_url: Destination stored on InAppNotification.link_url.

    Returns:
        str: Root-relative path for redirect, or empty string if unset.
    """
    if not link_url:
        return ""

    if link_url.startswith("/") and not link_url.startswith("//"):
        return link_url

    parsed = urlparse(link_url)
    if parsed.scheme and parsed.netloc:
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"
        return path

    return ""


def build_protocol_notification_path(protocol) -> str:
    """
    Build relative path for a protocol public detail notification link.

    Args:
        protocol: Protocol instance.

    Returns:
        str: Root-relative URL path.
    """
    return reverse(
        "protocols:protocol_public_detail",
        kwargs={"external_id": protocol.external_id},
    )


def build_workorder_notification_path(work_order) -> str:
    """
    Build relative path for a work order notification link.

    Args:
        work_order: WorkOrder instance.

    Returns:
        str: Root-relative URL path.
    """
    return reverse(
        "protocols:workorder_detail",
        kwargs={"pk": work_order.pk},
    )


def notification_go_path(notification_id: int) -> str:
    """
    Build path to the mark-read-and-redirect view for a notification.

    Args:
        notification_id: InAppNotification primary key.

    Returns:
        str: Root-relative URL path.
    """
    return reverse(
        "pages:notifications_go",
        kwargs={"pk": notification_id},
    )
