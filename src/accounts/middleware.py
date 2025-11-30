"""
Middleware for enforcing veterinarian profile completion.

This middleware ensures that all authenticated veterinarians have completed
their professional profile before accessing any protected pages.
"""

from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin


class VeterinarianProfileRequiredMiddleware(MiddlewareMixin):
    """
    Middleware that enforces veterinarian profile completion.

    Redirects authenticated veterinarians without complete profiles to the
    profile completion page. Allows access to whitelisted URLs.
    """

    # URLs that veterinarians can access without complete profile
    WHITELISTED_URLS = [
        "/accounts/veterinarian/complete-profile/",
        "/accounts/logout/",
        "/accounts/password-reset/",
        "/accounts/resend-verification/",
        "/accounts/histopathologist/create/",  # Admin-only view
        "/admin/",
        "/static/",
        "/media/",
    ]

    def process_request(self, request):
        """
        Process the request and redirect if profile is incomplete.

        Args:
            request: HTTP request object

        Returns:
            HttpResponse or None: Redirect response if profile incomplete, None otherwise
        """
        # Skip if user is not authenticated
        if not request.user.is_authenticated:
            return None

        # Skip if user is not a veterinarian or is admin
        if not request.user.is_veterinarian or request.user.is_admin_user:
            return None

        # Skip if accessing whitelisted URLs
        if self._is_whitelisted_url(request.path):
            return None

        # Check if veterinarian has a complete profile
        if not self._has_complete_profile(request.user):
            return redirect("accounts:complete_profile")

        return None

    def _is_whitelisted_url(self, path):
        """
        Check if the URL is whitelisted for veterinarians without complete profiles.

        Args:
            path: URL path to check

        Returns:
            bool: True if URL is whitelisted, False otherwise
        """
        return any(path.startswith(url) for url in self.WHITELISTED_URLS)

    def _has_complete_profile(self, user):
        """
        Check if veterinarian has a complete profile.

        Args:
            user: User instance to check

        Returns:
            bool: True if profile is complete, False otherwise
        """
        try:
            veterinarian = user.veterinarian_profile
            # Check if profile has all required fields
            return (
                veterinarian.first_name
                and veterinarian.last_name
                and veterinarian.license_number
                and veterinarian.phone
                and veterinarian.email
            )
        except Exception:
            # No veterinarian profile exists
            return False
