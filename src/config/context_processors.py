"""
Context processors for templates.
"""

from django.conf import settings
from django.urls import reverse


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
