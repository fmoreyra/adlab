from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import User


def role_required(*roles):
    """
    Decorator to restrict access to views based on user role.

    Usage:
        @role_required(User.Role.VETERINARIO)
        def my_view(request):
            ...

        @role_required(User.Role.PERSONAL_LAB, User.Role.HISTOPATOLOGO)
        def another_view(request):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role in roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied

        return wrapper

    return decorator


def veterinarian_required(view_func):
    """Decorator to restrict access to veterinarians only."""
    return role_required(User.Role.VETERINARIO)(view_func)


def lab_staff_required(view_func):
    """Decorator to restrict access to laboratory staff only."""
    return role_required(User.Role.PERSONAL_LAB, User.Role.HISTOPATOLOGO)(
        view_func
    )


def histopathologist_required(view_func):
    """Decorator to restrict access to histopathologists only."""
    return role_required(User.Role.HISTOPATOLOGO)(view_func)


def admin_required(view_func):
    """Decorator to restrict access to administrators only."""
    return role_required(User.Role.ADMIN)(view_func)


def ajax_required(view_func):
    """Decorator to ensure request is AJAX."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper
