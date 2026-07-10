"""
Middleware for enforcing veterinarian profile completion and lab staff onboarding.

Veterinarians must complete their professional profile before accessing
protected pages. Laboratory staff must upload a digital signature during
onboarding before using the application.
"""

from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

from accounts.models import Veterinarian
from accounts.report_access import user_requires_lab_staff_signature

# JSON API routes must never receive HTML redirects (fetch clients, debug toolbar).
API_PATH_PREFIX = "/api/"


class VeterinarianProfileRequiredMiddleware(MiddlewareMixin):
    """
    Middleware that enforces veterinarian profile completion.

    Redirects authenticated veterinarians without complete profiles to the
    profile completion page. Allows access to whitelisted URLs.
    """

    WHITELISTED_URLS = [
        "/accounts/veterinarian/pending-approval/",
        "/accounts/veterinarian/complete-profile/",
        "/accounts/logout/",
        "/accounts/password-reset/",
        "/accounts/resend-verification/",
        "/accounts/verify-email/",
        "/accounts/lab-staff/create/",
        "/admin/",
        "/static/",
        "/media/",
    ]

    def process_request(self, request):
        """Redirect veterinarians with incomplete profiles."""
        if not request.user.is_authenticated:
            return None

        if not request.user.is_veterinarian or request.user.is_admin_user:
            return None

        if self._is_whitelisted_url(request.path):
            return None

        if request.path.startswith(API_PATH_PREFIX):
            return None

        if not self._has_complete_profile(request.user):
            return redirect("accounts:complete_profile")

        return None

    def _is_whitelisted_url(self, path):
        """Return True if the path is accessible without a complete profile."""
        return any(path.startswith(url) for url in self.WHITELISTED_URLS)

    def _has_complete_profile(self, user):
        """Return True when the veterinarian profile is complete."""
        if not Veterinarian.objects.filter(user=user).exists():
            return False

        return user.veterinarian_profile.is_profile_complete_for_access()


class LabStaffSignatureRequiredMiddleware(MiddlewareMixin):
    """
    Middleware that enforces digital signature upload for laboratory staff.

    Redirects authenticated lab staff without a signature to the upload form.
    """

    WHITELISTED_URLS = [
        "/accounts/lab-staff/signature/",
        "/accounts/logout/",
        "/accounts/password-reset/",
        "/accounts/password-reset/confirm/",
        "/accounts/resend-verification/",
        "/accounts/verify-email/",
        "/accounts/lab-staff/create/",
        "/accounts/histopathologist/create/",
        "/admin/",
        "/static/",
        "/media/",
    ]

    def process_request(self, request):
        """Redirect lab staff missing a digital signature."""
        if not request.user.is_authenticated:
            return None

        if not request.user.is_lab_staff or request.user.is_admin_user:
            return None

        if self._is_whitelisted_url(request.path):
            return None

        if request.path.startswith(API_PATH_PREFIX):
            return None

        if user_requires_lab_staff_signature(request.user):
            return redirect("accounts:lab_staff_signature")

        return None

    def _is_whitelisted_url(self, path):
        """Return True if the path is accessible without a signature."""
        return any(path.startswith(url) for url in self.WHITELISTED_URLS)
