"""
Custom permission mixins for class-based views.

These mixins provide role-based access control for different user types
in the laboratory system.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _

from accounts.report_access import (
    get_report_signature_redirect_url,
    report_signature_required_message,
    user_requires_report_signature,
)
from protocols.models import Protocol


class ApiLoginRequiredMixin(LoginRequiredMixin):
    """
    LoginRequiredMixin that returns JSON 401 for /api/ paths.

    Avoids HTML login redirects that break fetch().json() and DJDT panels.
    """

    def handle_no_permission(self):
        """Return JSON for API routes; redirect for normal pages."""
        if self.request.path.startswith("/api/"):
            return JsonResponse(
                {"error": "Autenticación requerida"},
                status=401,
            )
        return super().handle_no_permission()


class ReportSignatureRequiredMixin:
    """
    Require a digital signature for lab staff who create pathology reports.

    Veterinarians and other roles are not checked.
    """

    def dispatch(self, request, *args, **kwargs):
        """Redirect lab staff without signature to the upload form."""
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if request.user.is_lab_staff and user_requires_report_signature(
            request.user
        ):
            messages.error(request, report_signature_required_message())
            return redirect(get_report_signature_redirect_url())

        return super().dispatch(request, *args, **kwargs)


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires the user to be laboratory staff.

    Used for views that only laboratory staff should access,
    such as reception, processing, and report management.
    """

    def test_func(self):
        """Test if user is laboratory staff."""
        return self.request.user.is_lab_staff

    def get_permission_denied_message(self):
        """Return custom permission denied message."""
        return _("No tiene permisos para acceder a esta función.")

    def handle_no_permission(self):
        """Handle permission denied by showing 403 error page with message."""
        from django.contrib import messages
        from django.http import HttpResponseForbidden
        from django.template.loader import render_to_string

        # If user is not authenticated, let LoginRequiredMixin handle it
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()

        # If user is authenticated but not staff, show 403
        messages.error(self.request, self.get_permission_denied_message())
        return HttpResponseForbidden(
            render_to_string(
                "403.html", {"user": self.request.user}, request=self.request
            )
        )


class VeterinarianRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires the user to be a veterinarian.

    Used for views that only veterinarians should access,
    such as protocol creation and veterinarian profile management.
    """

    def test_func(self):
        """Test if user is a veterinarian."""
        return self.request.user.is_veterinarian

    def get_permission_denied_message(self):
        """Return custom permission denied message."""
        return _("Esta función está disponible solo para veterinarios.")

    def handle_no_permission(self):
        """Handle permission denied by showing 403 error page with message."""
        from django.contrib import messages
        from django.http import HttpResponseForbidden
        from django.template.loader import render_to_string

        # If user is not authenticated, let LoginRequiredMixin handle it
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()

        # If user is authenticated but not a veterinarian, show 403
        messages.error(self.request, self.get_permission_denied_message())
        return HttpResponseForbidden(
            render_to_string(
                "403.html", {"user": self.request.user}, request=self.request
            )
        )


def user_can_view_work_order_detail(user):
    """
    Return whether the user may open work order detail URLs.

    Matches ``WorkOrderStaffRequiredMixin`` (Django ``is_staff``).
    """
    return user.is_authenticated and user.is_staff


def user_can_access_work_order(user, work_order):
    """
    Return whether the user may view a work order (detail/PDF).

    Laboratory billing staff (``is_staff``) and the owning veterinarian
    may access their orders.
    """
    if not user.is_authenticated:
        return False

    if user.is_staff:
        return True

    if not user.is_veterinarian:
        return False

    try:
        from accounts.models import Veterinarian

        return user.veterinarian_profile.pk == work_order.veterinarian_id
    except Veterinarian.DoesNotExist:
        return False


def user_can_view_protocol_processing(user, protocol):
    """
    Return whether the user may open protocol processing status.

    Matches ``StaffRequiredMixin`` (``User.is_lab_staff``). Veterinarians
    and protocols still awaiting reception cannot access processing views.
    """
    if not user.is_authenticated or not user.is_lab_staff:
        return False

    return protocol.status in {
        Protocol.Status.RECEIVED,
        Protocol.Status.PROCESSING,
        Protocol.Status.READY,
        Protocol.Status.REPORT_SENT,
    }


class WorkOrderStaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Restrict work order views to users with Django ``is_staff=True``.

    This is intentionally separate from ``StaffRequiredMixin`` (lab reception
    and processing), which checks ``User.is_lab_staff`` by role.

    A PERSONAL_LAB user without ``is_staff`` can receive and process samples but
    cannot open work order URLs until an administrator enables "Staff status"
    on their user in Django admin (Users → Staff status / is_staff).

    Veterinarians use ``WorkOrderAccessMixin`` for read-only access to their OTs.
    """

    def test_func(self):
        """Allow only Django staff users (``User.is_staff``)."""
        return user_can_view_work_order_detail(self.request.user)

    def get_permission_denied_message(self):
        """Return custom permission denied message."""
        return _("No tiene permisos para acceder a esta función.")

    def handle_no_permission(self):
        """Handle permission denied by redirecting to protocols list with message."""
        from django.contrib import messages
        from django.shortcuts import redirect

        messages.error(self.request, self.get_permission_denied_message())
        return redirect("protocols:protocol_list")


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires the user to be an admin.

    Used for views that only administrators should access,
    such as system administration and user management.
    """

    def test_func(self):
        """Test if user is an admin."""
        return self.request.user.is_admin_user

    def get_permission_denied_message(self):
        """Return custom permission denied message."""
        return _("Esta función está disponible solo para administradores.")

    def handle_no_permission(self):
        """Handle permission denied by showing 403 error page with message."""
        from django.contrib import messages
        from django.http import HttpResponseForbidden
        from django.template.loader import render_to_string

        # If user is not authenticated, let LoginRequiredMixin handle it
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()

        # If user is authenticated but not an admin, show 403
        messages.error(self.request, self.get_permission_denied_message())
        return HttpResponseForbidden(
            render_to_string(
                "403.html", {"user": self.request.user}, request=self.request
            )
        )


class ProtocolOwnerOrStaffMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that allows access if user owns the protocol or is lab staff.

    Used for protocol detail, edit, and delete views where
    veterinarians can access their own protocols and lab staff can access all.
    """

    def test_func(self):
        """Test if user owns the protocol or is lab staff."""
        if self.request.user.is_lab_staff or self.request.user.is_admin_user:
            return True

        if not self.request.user.is_veterinarian:
            return False

        # Get protocol from URL kwargs
        protocol_pk = self.kwargs.get("pk")
        if not protocol_pk:
            return False

        try:
            protocol = get_object_or_404(Protocol, pk=protocol_pk)
            return protocol.veterinarian.user == self.request.user
        except Protocol.DoesNotExist:
            return False

    def get_permission_denied_message(self):
        """Return custom permission denied message."""
        return _("No tiene permisos para acceder a este protocolo.")

    def handle_no_permission(self):
        """Handle permission denied by showing 403 error page with message."""
        from django.contrib import messages
        from django.http import HttpResponseForbidden
        from django.template.loader import render_to_string

        # If user is not authenticated, let LoginRequiredMixin handle it
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()

        # If user is authenticated but doesn't have access, show 403
        messages.error(self.request, self.get_permission_denied_message())
        return HttpResponseForbidden(
            render_to_string(
                "403.html", {"user": self.request.user}, request=self.request
            )
        )


class VeterinarianProfileRequiredMixin(
    LoginRequiredMixin, UserPassesTestMixin
):
    """
    Mixin that requires the user to have a complete veterinarian profile.

    Used for views that require veterinarian profile information,
    such as protocol creation and veterinarian-specific features.
    """

    def test_func(self):
        """Test if user has a complete veterinarian profile."""
        if not self.request.user.is_veterinarian:
            return False

        try:
            veterinarian = self.request.user.veterinarian_profile
            return veterinarian.is_profile_complete_for_access()
        except Exception:
            return False

    def get_permission_denied_message(self):
        """Return custom permission denied message."""
        return _("Debe completar su perfil de veterinario primero.")

    def handle_no_permission(self):
        """Handle permission denied by showing 403 error page with message."""
        from django.contrib import messages
        from django.http import HttpResponseForbidden
        from django.template.loader import render_to_string

        # If user is not authenticated, let LoginRequiredMixin handle it
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()

        # If user is authenticated but doesn't have complete profile, show 403
        messages.error(self.request, self.get_permission_denied_message())
        return HttpResponseForbidden(
            render_to_string(
                "403.html", {"user": self.request.user}, request=self.request
            )
        )


class ReportAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that allows access to reports based on user role.

    - Staff can access all reports
    - Veterinarians can access reports for their protocols
    - Laboratory staff can access reports they created or are assigned to (if can_create_reports)
    """

    def test_func(self):
        """Test if user has access to the report."""
        if self.request.user.is_lab_staff:
            return True

        # Get report from URL kwargs
        report_pk = self.kwargs.get("pk")
        if not report_pk:
            return False

        try:
            from protocols.models import Report

            report = get_object_or_404(Report, pk=report_pk)

            if self.request.user.is_veterinarian:
                # Veterinarians can access reports for their protocols
                return report.protocol.veterinarian.user == self.request.user

            if self.request.user.is_lab_staff:
                # Laboratory staff can access reports they created or are assigned to
                try:
                    # Check both LaboratoryStaff and Histopathologist profiles
                    if hasattr(self.request.user, "laboratory_staff_profile"):
                        staff_profile = (
                            self.request.user.laboratory_staff_profile
                        )
                        return (
                            report.laboratory_staff == staff_profile
                            or report.histopathologist == staff_profile
                        )
                    elif hasattr(
                        self.request.user, "histopathologist_profile"
                    ):
                        return (
                            report.histopathologist
                            == self.request.user.histopathologist_profile
                        )
                    return False
                except Exception:
                    # Staff member doesn't have a profile
                    return False

            return False
        except Exception:
            return False

    def get_permission_denied_message(self):
        """Return custom permission denied message."""
        return _("No tiene permisos para acceder a este informe.")

    def handle_no_permission(self):
        """Handle permission denied by showing 403 error page with message."""
        from django.contrib import messages
        from django.http import HttpResponseForbidden
        from django.template.loader import render_to_string

        # If user is not authenticated, let LoginRequiredMixin handle it
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()

        # If user is authenticated but doesn't have access, show 403
        messages.error(self.request, self.get_permission_denied_message())
        return HttpResponseForbidden(
            render_to_string(
                "403.html", {"user": self.request.user}, request=self.request
            )
        )


class WorkOrderAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Allow Django staff or the veterinarian who owns the work order.
    """

    def test_func(self):
        """Test work order access for staff or owning veterinarian."""
        from protocols.models import WorkOrder

        work_order = WorkOrder.objects.filter(pk=self.kwargs.get("pk")).first()
        if work_order is None:
            return False

        return user_can_access_work_order(self.request.user, work_order)

    def get_permission_denied_message(self):
        """Return custom permission denied message."""
        return _("No tiene permisos para acceder a esta orden de trabajo.")

    def handle_no_permission(self):
        """Redirect with an error message."""
        from django.contrib import messages
        from django.shortcuts import redirect

        if not self.request.user.is_authenticated:
            return super().handle_no_permission()

        messages.error(self.request, self.get_permission_denied_message())
        return redirect("protocols:protocol_list")
