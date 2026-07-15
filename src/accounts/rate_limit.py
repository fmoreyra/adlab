"""
Rate limiting helpers for public authentication endpoints.

Uses django-ratelimit with the default Redis/LocMem cache backend.
"""

from django.contrib import messages
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django_ratelimit.decorators import ratelimit

DEFAULT_RATE_LIMIT_MESSAGE = _(
    "Demasiados intentos. Por favor espere unos minutos e intente de nuevo."
)

LOGIN_RATE = "10/m"
REGISTER_RATE = "3/h"
PASSWORD_RESET_RATE = "3/h"
RESEND_VERIFICATION_RATE = "3/h"


def ratelimit_post(*, key, rate):
    """
    Apply a POST-only IP/content rate limit decorator to a class-based view.

    Args:
        key: django-ratelimit key (e.g. ``ip``, ``post:email``)
        rate: Limit string (e.g. ``10/m``, ``3/h``)

    Returns:
        method_decorator configured for ``post``
    """
    return method_decorator(
        ratelimit(key=key, rate=rate, method="POST", block=False),
        name="post",
    )


def ratelimit_get(*, key, rate):
    """
    Apply a GET-only rate limit decorator to a class-based view.

    Args:
        key: django-ratelimit key
        rate: Limit string

    Returns:
        method_decorator configured for ``get``
    """
    return method_decorator(
        ratelimit(key=key, rate=rate, method="GET", block=False),
        name="get",
    )


class RateLimitedFormMixin:
    """
    Mixin that shows a Spanish form error when django-ratelimit blocks a request.

    Expects ``rate_limit_message`` on the view class (optional override).
    """

    rate_limit_message = DEFAULT_RATE_LIMIT_MESSAGE

    def post(self, request, *args, **kwargs):
        """Return form error when POST rate limit exceeded."""
        if getattr(request, "limited", False):
            messages.error(request, self.rate_limit_message)
            # CreateView.get_context_data expects self.object (normally set in post).
            if not hasattr(self, "object"):
                self.object = None
            return self.form_invalid(self.get_form())
        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Return form page when GET rate limit exceeded (no side effects)."""
        if getattr(request, "limited", False):
            messages.error(request, self.rate_limit_message)
            if not hasattr(self, "object"):
                self.object = None
            return self.render_to_response(self.get_context_data())
        return super().get(request, *args, **kwargs)
