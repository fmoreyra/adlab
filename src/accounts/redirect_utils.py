"""Helpers for safe post-login and post-auth redirects."""

from urllib.parse import urlparse

from django.utils.http import url_has_allowed_host_and_scheme


def resolve_safe_redirect(request, url: str, default: str = "") -> str:
    """
    Return a safe redirect target from user-supplied ``next`` URL or path.

    Accepts same-host absolute URLs and root-relative paths. Rejects external
    hosts and protocol-relative URLs (``//``).

    Args:
        request: Current HTTP request (for host/scheme checks).
        url: Candidate redirect from query string or form field.
        default: Value when ``url`` is missing or unsafe.

    Returns:
        str: Safe path or URL to redirect to.
    """
    if not url:
        return default

    if url_has_allowed_host_and_scheme(
        url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        parsed = urlparse(url)
        if parsed.scheme:
            path = parsed.path or "/"
            if parsed.query:
                path = f"{path}?{parsed.query}"
            return path
        return url

    if url.startswith("/") and not url.startswith("//"):
        return url

    return default
