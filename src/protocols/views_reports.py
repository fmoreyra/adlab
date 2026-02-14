"""
Views for report generation and management.
"""

import logging

from django.contrib import messages
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
    View,
)

from accounts.mixins import StaffRequiredMixin
from protocols.forms_reports import (
    ReportCreateForm,
    ReportSendForm,
)
from protocols.models import Protocol, Report
from protocols.services.email_service import EmailNotificationService
from protocols.services.pdf_service import PDFGenerationService
from protocols.services.report_service import ReportGenerationService

logger = logging.getLogger(__name__)

# =============================================================================
# REPORT LIST AND SEARCH
# =============================================================================
# CLASS-BASED VIEWS
# =============================================================================


class ReportPendingListView(StaffRequiredMixin, ListView):
    """
    List protocols that are ready for report generation.
    """

    model = Protocol
    template_name = "protocols/reports/pending_list.html"
    context_object_name = "protocols"

    def get_queryset(self):
        """Get protocols ready for report generation."""
        # Protocols that are READY status and don't have reports yet
        protocols = (
            Protocol.objects.filter(status=Protocol.Status.READY)
            .select_related(
                "veterinarian__user",
                "cytology_sample",
                "histopathology_sample",
            )
            .prefetch_related(
                "histopathology_sample__cassettes",
                "slides",
            )
            .order_by("-reception_date")
        )

        # Filter out protocols that already have reports
        protocols_without_reports = []
        for protocol in protocols:
            if not protocol.reports.exists():
                protocols_without_reports.append(protocol)

        return protocols_without_reports

    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context["title"] = _("Protocolos Pendientes de Informe")
        return context


class ReportHistoryView(StaffRequiredMixin, ListView):
    """
    View history of generated reports.
    """

    model = Report
    template_name = "protocols/reports/history.html"
    context_object_name = "reports"
    paginate_by = 20

    def get_queryset(self):
        """Get all reports ordered by creation date."""
        return Report.objects.select_related(
            "protocol__veterinarian__user",
            "laboratory_staff__user",
            "veterinarian__user",
        ).order_by("-created_at")


class ReportCreateView(StaffRequiredMixin, CreateView):
    """
    Create a new report for a protocol with service integration.
    """

    model = Report
    form_class = ReportCreateForm
    template_name = "protocols/reports/create.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_service = ReportGenerationService()

    def get_success_url(self):
        """Redirect to report edit after creation."""
        if self.object and hasattr(self.object, "pk"):
            return reverse(
                "protocols:report_edit", kwargs={"pk": self.object.pk}
            )
        return reverse("protocols:report_pending_list")

    def get_context_data(self, **kwargs):
        """Add protocol to context."""
        context = super().get_context_data(**kwargs)
        context["protocol"] = self.get_protocol()
        return context

    def get_protocol(self):
        """Get the protocol for this report."""
        return get_object_or_404(
            Protocol.objects.select_related(
                "veterinarian__user",
                "cytology_sample",
                "histopathology_sample",
            ).prefetch_related(
                "histopathology_sample__cassettes",
                "slides",
            ),
            pk=self.kwargs.get("protocol_id"),
        )

    def form_valid(self, form):
        """Create report using service with early returns."""
        protocol = self.get_protocol()

        # Early return for protocol validation
        is_valid, error_message = (
            self.report_service.validate_protocol_for_report(protocol)
        )
        if not is_valid:
            messages.error(self.request, error_message)
            return redirect("protocols:report_pending_list")

        # Create report using service with form data
        success, report, error_message = self.report_service.create_report(
            protocol,
            self.request.user.lab_staff_profile,
            form.cleaned_data,
        )

        if not success:
            messages.error(
                self.request, f"Error al crear informe: {error_message}"
            )
            return redirect("protocols:report_pending_list")

        self.object = report
        messages.success(
            self.request,
            _("Informe creado exitosamente. Puede editarlo ahora."),
        )

        return redirect(self.get_success_url())


class ReportEditView(StaffRequiredMixin, UpdateView):
    """
    Edit an existing report with service integration.
    """

    model = Report
    form_class = ReportCreateForm
    template_name = "protocols/reports/edit.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_service = ReportGenerationService()

    def dispatch(self, request, *args, **kwargs):
        """Check if report can be edited before processing the request."""
        self.object = self.get_object()

        # Check if report is finalized - finalized reports cannot be edited
        if self.object.status == Report.Status.FINALIZED:
            messages.warning(
                request, _("No se puede editar un informe finalizado.")
            )
            return redirect("protocols:report_detail", pk=self.object.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """Redirect to report detail after editing."""
        return reverse(
            "protocols:report_detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        """Add protocol to context."""
        context = super().get_context_data(**kwargs)
        context["protocol"] = self.object.protocol
        return context

    def form_valid(self, form):
        """Update report using service with early returns."""
        # Validate report content
        content_data = {
            "macroscopic_observations": form.cleaned_data.get(
                "macroscopic_observations", ""
            ),
            "microscopic_observations": form.cleaned_data.get(
                "microscopic_observations", ""
            ),
            "diagnosis": form.cleaned_data.get("diagnosis", ""),
            "comments": form.cleaned_data.get("comments", ""),
            "recommendations": form.cleaned_data.get("recommendations", ""),
        }

        is_valid, errors = self.report_service.validate_report_content(
            content_data
        )
        if not is_valid:
            for error in errors:
                messages.error(self.request, error)
            return self.form_invalid(form)

        # Update report using service
        success, error_message = self.report_service.update_report_content(
            self.object, content_data, self.request.user
        )

        if not success:
            messages.error(
                self.request, f"Error al actualizar informe: {error_message}"
            )
            return self.form_invalid(form)

        messages.success(self.request, _("Informe actualizado exitosamente."))

        return redirect(self.get_success_url())


class ReportDetailView(DetailView):
    """
    View report details.
    """

    model = Report
    template_name = "protocols/reports/detail.html"
    context_object_name = "report"

    def dispatch(self, request, *args, **kwargs):
        """Check permissions before processing the request."""
        if not request.user.is_authenticated:
            return redirect("accounts:login")

        # Get the report object
        self.object = self.get_object()

        # Check permissions
        is_owner = False
        if hasattr(request.user, "veterinarian_profile"):
            is_owner = (
                request.user.veterinarian_profile == self.object.veterinarian
            )

        if not (request.user.is_lab_staff or is_owner):
            messages.error(
                request, _("No tiene permisos para ver este informe.")
            )
            return redirect("protocols:protocol_list")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Get report with related objects."""
        return Report.objects.select_related(
            "protocol__veterinarian__user",
            "laboratory_staff__user",
            "veterinarian__user",
        ).prefetch_related(
            "protocol__histopathology_sample__cassettes",
            "protocol__slides",
        )


class ReportFinalizeView(StaffRequiredMixin, View):
    """
    Finalize a report (mark as ready for sending).
    """

    def post(self, request, *args, **kwargs):
        """Finalize the report."""
        report = get_object_or_404(Report, pk=self.kwargs["pk"])

        if report.status != Report.Status.DRAFT:
            messages.error(
                request, _("Solo se pueden finalizar informes en borrador.")
            )
            return redirect("protocols:report_detail", pk=report.pk)

        # Finalize the report
        report.finalize()

        messages.success(request, _("Informe finalizado exitosamente."))

        return redirect("protocols:report_detail", pk=report.pk)


class ReportPDFView(View):
    """
    Generate PDF version of a report with service integration.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pdf_service = PDFGenerationService()

    def dispatch(self, request, *args, **kwargs):
        """Check permissions before processing the request."""
        if not request.user.is_authenticated:
            return redirect("accounts:login")

        # Get the report object
        report = get_object_or_404(Report, pk=self.kwargs["pk"])

        # Check permissions
        is_owner = False
        if hasattr(request.user, "veterinarian_profile"):
            is_owner = request.user.veterinarian_profile == report.veterinarian

        if not (request.user.is_lab_staff or is_owner):
            messages.error(
                request, _("No tiene permisos para ver este informe.")
            )
            return redirect("protocols:protocol_list")

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Generate and return PDF report using service."""
        report = get_object_or_404(Report, pk=self.kwargs["pk"])

        if report.status == Report.Status.DRAFT:
            messages.error(
                request,
                _("No se puede generar PDF de un informe en borrador."),
            )
            return redirect("protocols:report_detail", pk=report.pk)

        # Generate PDF using service
        pdf_buffer, pdf_hash = self.pdf_service.generate_report_pdf(report)

        filename = f"informe_{report.protocol.protocol_number}.pdf"
        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=filename,
            content_type="application/pdf",
        )


class ReportSendView(StaffRequiredMixin, FormView):
    """
    Send a finalized report to the veterinarian with service integration.
    """

    form_class = ReportSendForm
    template_name = "protocols/reports/send.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_service = ReportGenerationService()
        self.email_service = EmailNotificationService()

    def dispatch(self, request, *args, **kwargs):
        """Check if report can be sent before processing the request."""
        report = self.get_report()

        # Check if report is finalized - only finalized reports can be sent
        if report.status != Report.Status.FINALIZED:
            messages.error(
                request, _("Solo se pueden enviar informes finalizados.")
            )
            return redirect("protocols:report_detail", pk=report.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """Redirect to report detail after sending."""
        return reverse(
            "protocols:report_detail", kwargs={"pk": self.kwargs["pk"]}
        )

    def get_context_data(self, **kwargs):
        """Add report to context."""
        context = super().get_context_data(**kwargs)
        context["report"] = self.get_report()
        return context

    def get_report(self):
        """Get the report to send."""
        return get_object_or_404(Report, pk=self.kwargs["pk"])

    def form_valid(self, form):
        """Send the report using service with early returns."""
        report = self.get_report()

        # Early return for status validation
        if report.status != Report.Status.FINALIZED:
            messages.error(
                self.request, _("Solo se pueden enviar informes finalizados.")
            )
            return redirect("protocols:report_detail", pk=report.pk)

        # Send report using service
        success, error_message = self.report_service.send_report(
            report, self.request.user
        )

        if not success:
            messages.error(
                self.request, f"Error al enviar informe: {error_message}"
            )
            return redirect("protocols:report_detail", pk=report.pk)

        # Send email notification using service
        self.email_service.send_report_ready_notification(report)

        messages.success(self.request, _("Informe enviado exitosamente."))
        return redirect(self.get_success_url())


def generate_report_pdf(report):
    """
    Standalone function to generate PDF for a report.
    Used by tests and other parts of the system.

    Args:
        report: Report instance

    Returns:
        tuple: (pdf_buffer, pdf_hash)
    """
    pdf_service = PDFGenerationService()
    return pdf_service.generate_report_pdf(report)
