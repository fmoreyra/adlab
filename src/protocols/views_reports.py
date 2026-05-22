"""
Views for report generation and management.
"""

import logging

from django.contrib import messages
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
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

from accounts.mixins import (
    ProtocolOwnerOrStaffMixin,
    ReportSignatureRequiredMixin,
    StaffRequiredMixin,
    VeterinarianRequiredMixin,
)
from accounts.report_access import (
    get_report_signature_redirect_url,
    report_signature_required_message,
    report_signer_missing_message,
    report_signer_signature_missing_message,
    user_can_view_report_images,
    user_requires_report_signature,
)
from protocols.forms_reports import (
    CassetteObservationFormSet,
    ReportCreateForm,
    ReportImageFormSet,
    ReportSendForm,
)
from protocols.models import Protocol, Report, ReportImage
from protocols.protocol_detail_context import _get_latest_report
from protocols.services.email_service import EmailNotificationService
from protocols.services.pdf_service import (
    PDFGenerationError,
    PDFGenerationService,
)
from protocols.services.report_service import ReportGenerationService

logger = logging.getLogger(__name__)

# =============================================================================
# REPORT LIST AND SEARCH
# =============================================================================
# CLASS-BASED VIEWS
# =============================================================================


class ReportPendingListView(
    ReportSignatureRequiredMixin, StaffRequiredMixin, ListView
):
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


class VeterinarianReportListView(VeterinarianRequiredMixin, ListView):
    """
    List finalized/sent reports for the logged-in veterinarian.
    """

    model = Report
    template_name = "protocols/reports/vet_history.html"
    context_object_name = "reports"
    paginate_by = 20

    def get_queryset(self):
        """Return reports for protocols owned by the veterinarian."""
        veterinarian = self.request.user.veterinarian_profile
        return (
            Report.objects.filter(
                veterinarian=veterinarian,
                status__in=[Report.Status.FINALIZED, Report.Status.SENT],
            )
            .select_related(
                "protocol",
                "laboratory_staff__user",
                "histopathologist",
            )
            .order_by("-report_date", "-created_at")
        )

    def get_context_data(self, **kwargs):
        """Add page title."""
        context = super().get_context_data(**kwargs)
        context["title"] = _("Mis Informes")
        return context


class ReportHistoryView(
    ReportSignatureRequiredMixin, StaffRequiredMixin, ListView
):
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


class ReportCreateView(
    ReportSignatureRequiredMixin, StaffRequiredMixin, CreateView
):
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
        laboratory_staff = form.cleaned_data.get("laboratory_staff")
        if not laboratory_staff:
            messages.error(
                self.request,
                _("Debe seleccionar el personal responsable del informe."),
            )
            return redirect("protocols:report_pending_list")

        success, report, error_message = self.report_service.create_report(
            protocol,
            laboratory_staff,
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


class ReportEditView(
    ReportSignatureRequiredMixin, StaffRequiredMixin, UpdateView
):
    """
    Edit an existing report, cassette observations, and microscopy images.
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

        if self.object.status == Report.Status.FINALIZED:
            messages.warning(
                request, _("No se puede editar un informe finalizado.")
            )
            return redirect("protocols:report_detail", pk=self.object.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Pass protocol into the report form."""
        kwargs = super().get_form_kwargs()
        kwargs["protocol"] = self.object.protocol
        return kwargs

    def get_success_url(self):
        """Redirect to report detail after editing."""
        return reverse(
            "protocols:report_detail", kwargs={"pk": self.object.pk}
        )

    def get_cassette_formset(self):
        """Build cassette observation formset for the report."""
        kwargs = {"form_kwargs": {"report": self.object}}
        if self.request.method == "POST":
            return CassetteObservationFormSet(
                self.request.POST,
                instance=self.object,
                prefix="form",
                **kwargs,
            )
        return CassetteObservationFormSet(
            instance=self.object, prefix="form", **kwargs
        )

    def get_image_formset(self):
        """Build microscopy image formset for the report."""
        kwargs = {"form_kwargs": {"report": self.object}}
        if self.request.method == "POST":
            return ReportImageFormSet(
                self.request.POST,
                self.request.FILES,
                instance=self.object,
                prefix="images",
                **kwargs,
            )
        return ReportImageFormSet(
            instance=self.object, prefix="images", **kwargs
        )

    def get_context_data(self, **kwargs):
        """Add protocol, formsets, and page title."""
        context = super().get_context_data(**kwargs)
        context["protocol"] = self.object.protocol
        context["report"] = self.object
        context["title"] = _("Editar Informe")
        context.setdefault("formset", self.get_cassette_formset())
        context.setdefault("image_formset", self.get_image_formset())
        return context

    def post(self, request, *args, **kwargs):
        """Validate and save report, observations, and images together."""
        self.object = self.get_object()
        form = self.get_form()
        formset = self.get_cassette_formset()
        image_formset = self.get_image_formset()

        form_valid = form.is_valid()
        formset_valid = formset.is_valid()
        image_formset_valid = image_formset.is_valid()

        if not form_valid or not formset_valid or not image_formset_valid:
            return render(
                request,
                self.template_name,
                {
                    "form": form,
                    "formset": formset,
                    "image_formset": image_formset,
                    "protocol": self.object.protocol,
                    "report": self.object,
                    "title": _("Editar Informe"),
                },
            )

        content_data = {
            "laboratory_staff": form.cleaned_data.get("laboratory_staff"),
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
                messages.error(request, error)
            return render(
                request,
                self.template_name,
                {
                    "form": form,
                    "formset": formset,
                    "image_formset": image_formset,
                    "protocol": self.object.protocol,
                    "report": self.object,
                    "title": _("Editar Informe"),
                },
            )

        with transaction.atomic():
            success, error_message = self.report_service.update_report_content(
                self.object,
                content_data,
                request.user,
            )
            if not success:
                messages.error(
                    request,
                    _("Error al actualizar informe: %(error)s")
                    % {"error": error_message},
                )
                return render(
                    request,
                    self.template_name,
                    {
                        "form": form,
                        "formset": formset,
                        "image_formset": image_formset,
                        "protocol": self.object.protocol,
                        "report": self.object,
                        "title": _("Editar Informe"),
                    },
                )

            formset.save()
            image_formset.save()

        messages.success(request, _("Informe actualizado exitosamente."))
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
            "images__cassette",
            "images__slide",
            "cassette_observations__cassette",
        )

    def get_context_data(self, **kwargs):
        """Add permission flags for report actions in the template."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        report = self.object

        is_report_owner = False
        if hasattr(user, "veterinarian_profile"):
            is_report_owner = (
                user.veterinarian_profile.pk == report.veterinarian_id
            )

        context["is_report_owner"] = is_report_owner
        context["can_manage_report"] = user.is_lab_staff
        context["needs_report_signature"] = user_requires_report_signature(
            user
        )
        context["lab_staff_signature_url"] = (
            get_report_signature_redirect_url()
        )
        context["report_signer_ready"] = report.signer_has_signature()
        context["can_download_report_pdf"] = (
            report.status != Report.Status.DRAFT
            and bool(report.pdf_path)
            and (user.is_lab_staff or is_report_owner)
            and report.signer_has_signature()
        )
        context["protocol"] = report.protocol
        return context


class ReportFinalizeView(
    ReportSignatureRequiredMixin, StaffRequiredMixin, View
):
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

        if not report.get_signer():
            messages.error(request, report_signer_missing_message())
            return redirect("protocols:report_edit", pk=report.pk)

        if not report.signer_has_signature():
            messages.error(request, report_signer_signature_missing_message())
            return redirect("protocols:report_detail", pk=report.pk)

        pdf_service = PDFGenerationService()
        try:
            pdf_service.persist_report_pdf(report)
        except PDFGenerationError as exc:
            messages.error(request, str(exc))
            return redirect("protocols:report_edit", pk=report.pk)

        report.finalize()

        messages.success(
            request,
            _("Informe finalizado y PDF generado exitosamente."),
        )

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

        if request.user.is_lab_staff and user_requires_report_signature(
            request.user
        ):
            messages.error(request, report_signature_required_message())
            return redirect(get_report_signature_redirect_url())

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

        if not report.get_signer():
            messages.error(request, report_signer_missing_message())
            return redirect("protocols:report_detail", pk=report.pk)

        if not report.signer_has_signature():
            messages.error(request, report_signer_signature_missing_message())
            return redirect("protocols:report_detail", pk=report.pk)

        try:
            pdf_buffer, pdf_hash = self.pdf_service.generate_report_pdf(report)
        except PDFGenerationError as exc:
            messages.error(request, str(exc))
            return redirect("protocols:report_detail", pk=report.pk)

        filename = f"informe_{report.protocol.protocol_number}.pdf"
        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=filename,
            content_type="application/pdf",
        )


class ReportSendView(
    ReportSignatureRequiredMixin, StaffRequiredMixin, FormView
):
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

        # In-app notification (Step 21)
        if report.protocol:
            from protocols.services.notification_service import (
                NotificationService,
            )

            NotificationService().create_for_report_ready(report.protocol)

        messages.success(self.request, _("Informe enviado exitosamente."))
        return redirect(self.get_success_url())


def _get_protocol_report_for_images(protocol):
    """
    Return the latest report for a protocol that has microscopy images.

    Raises:
        Http404: If there is no report or no images
    """
    latest_report = _get_latest_report(protocol)
    if not latest_report or not latest_report.images.exists():
        raise Http404(_("No hay imágenes microscópicas para este protocolo."))
    return latest_report


class ProtocolReportImagesGalleryView(ProtocolOwnerOrStaffMixin, DetailView):
    """
    Gallery of microscopy images from the protocol's latest report.
    """

    model = Protocol
    template_name = "protocols/reports/protocol_images_gallery.html"
    context_object_name = "protocol"

    def get_queryset(self):
        """Prefetch report images for the protocol."""
        return Protocol.objects.select_related(
            "veterinarian__user",
        ).prefetch_related(
            "reports__images__cassette",
            "reports__images__slide",
        )

    def dispatch(self, request, *args, **kwargs):
        """Verify the protocol has viewable report images."""
        protocol = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])

        if not (
            request.user.is_lab_staff
            or request.user.is_admin_user
            or (
                request.user.is_veterinarian
                and protocol.veterinarian.user_id == request.user.pk
            )
        ):
            messages.error(
                request, _("No tiene permisos para ver este protocolo.")
            )
            return redirect("protocols:protocol_list")

        try:
            self.report = _get_protocol_report_for_images(protocol)
        except Http404:
            messages.info(
                request,
                _("Este protocolo aún no tiene imágenes microscópicas."),
            )
            return redirect("protocols:protocol_detail", pk=protocol.pk)

        if not user_can_view_report_images(
            request.user, protocol, self.report
        ):
            messages.error(
                request,
                _("No tiene permisos para ver las imágenes de este informe."),
            )
            return redirect("protocols:protocol_detail", pk=protocol.pk)

        self.protocol = protocol
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """Return the protocol loaded in dispatch."""
        return self.protocol

    def get_context_data(self, **kwargs):
        """Add report images and navigation context."""
        context = super().get_context_data(**kwargs)
        protocol = self.object
        images = self.report.images.select_related(
            "cassette", "slide"
        ).order_by("order", "created_at")

        context.update(
            {
                "title": _("Imágenes microscópicas"),
                "report": self.report,
                "report_images": images,
                "back_url": reverse(
                    "protocols:protocol_detail", kwargs={"pk": protocol.pk}
                ),
                "back_label": _("← Volver al protocolo"),
            }
        )
        return context


class ProtocolReportImageDetailView(ProtocolOwnerOrStaffMixin, DetailView):
    """
    Full-size view of a single microscopy image with metadata.
    """

    model = Protocol
    template_name = "protocols/reports/protocol_image_detail.html"
    context_object_name = "protocol"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        """Prefetch related report data."""
        return Protocol.objects.select_related("veterinarian__user")

    def dispatch(self, request, *args, **kwargs):
        """Resolve protocol, report, and image before the view runs."""
        self.protocol = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])
        self.report = _get_protocol_report_for_images(self.protocol)

        if not user_can_view_report_images(
            request.user, self.protocol, self.report
        ):
            messages.error(
                request,
                _("No tiene permisos para ver las imágenes de este informe."),
            )
            return redirect("protocols:protocol_detail", pk=self.protocol.pk)

        self.report_image = get_object_or_404(
            ReportImage,
            pk=kwargs["image_pk"],
            report=self.report,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """Return the protocol (image is on self.report_image)."""
        return self.protocol

    def get_context_data(self, **kwargs):
        """Add image, siblings, and navigation."""
        context = super().get_context_data(**kwargs)
        ordered_images = list(
            self.report.images.order_by("order", "created_at").values_list(
                "pk", flat=True
            )
        )
        current_index = ordered_images.index(self.report_image.pk)
        prev_image_pk = (
            ordered_images[current_index - 1] if current_index > 0 else None
        )
        next_image_pk = (
            ordered_images[current_index + 1]
            if current_index < len(ordered_images) - 1
            else None
        )

        context.update(
            {
                "title": _("Detalle de imagen microscópica"),
                "report": self.report,
                "report_image": self.report_image,
                "image_index": current_index + 1,
                "image_total": len(ordered_images),
                "prev_image_pk": prev_image_pk,
                "next_image_pk": next_image_pk,
                "gallery_url": reverse(
                    "protocols:protocol_report_images",
                    kwargs={"pk": self.protocol.pk},
                ),
                "back_url": reverse(
                    "protocols:protocol_detail",
                    kwargs={"pk": self.protocol.pk},
                ),
                "back_label": _("← Volver al protocolo"),
            }
        )
        return context


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
