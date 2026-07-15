"""
Cloudflare Turnstile verification for public registration.
"""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

TURNSTILE_VERIFY_URL = (
    "https://challenges.cloudflare.com/turnstile/v0/siteverify"
)


def is_turnstile_enabled() -> bool:
    """
    Return whether Turnstile keys are configured for registration.

    Returns:
        bool: True when both site and secret keys are set
    """
    return bool(settings.TURNSTILE_SITE_KEY and settings.TURNSTILE_SECRET_KEY)


def get_turnstile_site_key() -> str:
    """
    Return the public site key for template rendering.

    Returns:
        str: Site key or empty string when disabled
    """
    if not is_turnstile_enabled():
        return ""
    return settings.TURNSTILE_SITE_KEY


def verify_turnstile_token(token: str, remote_ip: str | None = None) -> bool:
    """
    Verify a Turnstile response token with Cloudflare.

    When Turnstile is not configured (local dev), verification is skipped.

    Args:
        token: Value from ``cf-turnstile-response`` POST field
        remote_ip: Client IP for optional remoteip parameter

    Returns:
        bool: True if token is valid or Turnstile is disabled
    """
    if not is_turnstile_enabled():
        return True

    if not token:
        return False

    payload = {
        "secret": settings.TURNSTILE_SECRET_KEY,
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    encoded = urllib.parse.urlencode(payload).encode()
    request = urllib.request.Request(
        TURNSTILE_VERIFY_URL,
        data=encoded,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = json.loads(response.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("Turnstile verification failed: %s", exc)
        return False

    return bool(body.get("success"))
