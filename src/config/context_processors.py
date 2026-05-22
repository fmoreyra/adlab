"""
Context processors for templates.
"""

from django.conf import settings
from django.urls import reverse

from pages.services.dashboard_announcement_service import get_cached_banner

DASHBOARD_URL_NAMES = frozenset(
    {
        "dashboard",
        "dashboard_veterinarian",
        "dashboard_lab_staff",
        "dashboard_admin",
        "dashboard_management",
    }
)


def sockudo_config(request):
    """
    Add Sockudo (Pusher-compatible) config for realtime notifications.

    Only added when SOCKUDO_ENABLED and user is authenticated.
    """
    if not getattr(settings, "SOCKUDO_ENABLED", False):
        return {"sockudo_config": None}
    if not request.user.is_authenticated:
        return {"sockudo_config": None}
    return {
        "sockudo_config": {
            "enabled": True,
            "app_key": settings.SOCKUDO_APP_KEY,
            "ws_host": settings.SOCKUDO_WS_HOST,
            "ws_port": settings.SOCKUDO_WS_PORT,
            "ws_use_tls": settings.SOCKUDO_WS_USE_TLS,
            "auth_endpoint": request.build_absolute_uri(
                reverse("pages_api:notifications:realtime_auth")
            ),
            "user_id": request.user.id,
        },
    }


def dashboard_announcement(request):
    """
    Inject cached dashboard banner on pages dashboard views only.

    Args:
        request: HTTP request

    Returns:
        dict: dashboard_announcement context key or empty
    """
    if not request.user.is_authenticated:
        return {"dashboard_announcement": None}

    match = getattr(request, "resolver_match", None)
    if match is None or match.url_name not in DASHBOARD_URL_NAMES:
        return {"dashboard_announcement": None}

    return {"dashboard_announcement": get_cached_banner()}
