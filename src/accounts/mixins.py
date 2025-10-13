"""
Custom permission mixins for class-based views.

These mixins provide role-based access control for different user types
in the laboratory system.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from protocols.models import Protocol


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires the user to be laboratory staff.

    Used for views that only laboratory staff should access,
    such as reception, processing, and report management.
    """

    def test_func(self):
        """Test if user is laboratory staff."""
        return self.request.user.is_staff

    def get_permission_denied_message(self):
        """Return custom permission denied message."""
        return _("No tiene permisos para acceder a esta función.")

    def handle_no_permission(self):
        """Handle permission denied by redirecting to home with message."""
        from django.contrib import messages
        from django.shortcuts import redirect

        messages.error(self.request, self.get_permission_denied_message())
        return redirect("home")


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


class WorkOrderStaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires the user to be staff, redirects to protocols list.
    """

    def test_func(self):
        """Test if user is staff."""
        return self.request.user.is_staff

    def get_permission_denied_message(self):
        """Return custom permission denied message."""
        return _("No tiene permisos para acceder a esta función.")

    def handle_no_permission(self):
        """Handle permission denied by redirecting to protocols list with message."""
        from django.contrib import messages
        from django.shortcuts import redirect

        messages.error(self.request, self.get_permission_denied_message())
        return redirect("protocols:protocol_list")


class HistopathologistRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires the user to be a histopathologist.

    Used for views that only histopathologists should access,
    such as report creation and editing.
    """

    def test_func(self):
        """Test if user is a histopathologist."""
        return self.request.user.is_histopathologist

    def get_permission_denied_message(self):
        """Return custom permission denied message."""
        return _("Esta función está disponible solo para histopatólogos.")


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


class ProtocolOwnerOrStaffMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that allows access if user owns the protocol or is staff.

    Used for protocol detail, edit, and delete views where
    veterinarians can access their own protocols and staff can access all.
    """

    def test_func(self):
        """Test if user owns the protocol or is staff."""
        if self.request.user.is_staff:
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
            # Check if profile is complete (has required fields)
            return (
                veterinarian.first_name
                and veterinarian.last_name
                and veterinarian.license_number
                and veterinarian.phone
                and veterinarian.email
            )
        except Exception:
            return False

    def get_permission_denied_message(self):
        """Return custom permission denied message."""
        return _("Debe completar su perfil de veterinario primero.")


class ReportAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that allows access to reports based on user role.

    - Staff can access all reports
    - Veterinarians can access reports for their protocols
    - Histopathologists can access reports they created or are assigned to
    """

    def test_func(self):
        """Test if user has access to the report."""
        if self.request.user.is_staff:
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

            if self.request.user.is_histopathologist:
                # Histopathologists can access reports they created or are assigned to
                return (
                    report.histopathologist
                    == self.request.user.histopathologist_profile
                    or report.created_by == self.request.user
                )

            return False
        except Exception:
            return False

    def get_permission_denied_message(self):
        """Return custom permission denied message."""
        return _("No tiene permisos para acceder a este informe.")


class WorkOrderAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that allows access to work orders based on user role.

    - Staff can access all work orders
    - Veterinarians can access work orders for their protocols
    """

    def test_func(self):
        """Test if user has access to the work order."""
        if self.request.user.is_staff:
            return True

        if not self.request.user.is_veterinarian:
            return False

        # Get work order from URL kwargs
        workorder_pk = self.kwargs.get("pk")
        if not workorder_pk:
            return False

        try:
            from protocols.models import WorkOrder

            work_order = get_object_or_404(WorkOrder, pk=workorder_pk)
            return work_order.veterinarian.user == self.request.user
        except Exception:
            return False

    def get_permission_denied_message(self):
        """Return custom permission denied message."""
        return _("No tiene permisos para acceder a esta orden de trabajo.")
