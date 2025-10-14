"""
Views for work order generation and management.
"""

import logging

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView, View
from django.views.generic.edit import FormView

from accounts.mixins import WorkOrderStaffRequiredMixin
from protocols.emails import send_work_order_notification
from protocols.forms_workorder import (
    ProtocolSelectionForm,
    WorkOrderCreateForm,
    WorkOrderFilterForm,
)
from protocols.models import (
    Protocol,
    WorkOrder,
)
from protocols.services.email_service import EmailNotificationService
from protocols.services.pdf_service import PDFGenerationService
from protocols.services.workorder_service import (
    WorkOrderCalculationService,
    WorkOrderCreationService,
)

logger = logging.getLogger(__name__)


# =============================================================================
# WORK ORDER LIST AND SEARCH
# =============================================================================
# CLASS-BASED VIEWS
# =============================================================================


class WorkOrderListView(WorkOrderStaffRequiredMixin, ListView):
    """
    List all work orders with filtering.
    """

    model = WorkOrder
    template_name = "protocols/workorder/list.html"
    context_object_name = "workorders"
    paginate_by = 20

    def get_queryset(self):
        """Get work orders with filtering."""
        queryset = WorkOrder.objects.select_related(
            "veterinarian__user",
            "created_by",
        ).order_by("-created_at")

        # Apply filters
        form = WorkOrderFilterForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get("status"):
                queryset = queryset.filter(status=form.cleaned_data["status"])
            if form.cleaned_data.get("veterinarian"):
                queryset = queryset.filter(
                    veterinarian=form.cleaned_data["veterinarian"]
                )
            if form.cleaned_data.get("date_from"):
                queryset = queryset.filter(
                    created_at__date__gte=form.cleaned_data["date_from"]
                )
            if form.cleaned_data.get("date_to"):
                queryset = queryset.filter(
                    created_at__date__lte=form.cleaned_data["date_to"]
                )

        return queryset

    def get_context_data(self, **kwargs):
        """Add filter form and work_orders to context."""
        context = super().get_context_data(**kwargs)
        context["filter_form"] = WorkOrderFilterForm(self.request.GET)
        context["title"] = _("Órdenes de Trabajo")
        context["work_orders"] = context[
            "object_list"
        ]  # Alias for template compatibility
        return context


class WorkOrderPendingProtocolsView(WorkOrderStaffRequiredMixin, ListView):
    """
    List protocols that are ready for work order generation.
    """

    model = Protocol
    template_name = "protocols/workorder/pending_protocols.html"
    context_object_name = "protocols"
    paginate_by = 20

    def get_queryset(self):
        """Get protocols ready for work order generation."""
        return (
            Protocol.objects.filter(
                status=Protocol.Status.READY,
                work_order__isnull=True,
            )
            .select_related(
                "veterinarian__user",
                "cytology_sample",
                "histopathology_sample",
            )
            .order_by("-reception_date")
        )

    def get_context_data(self, **kwargs):
        """Add title and protocols_by_vet to context."""
        context = super().get_context_data(**kwargs)
        context["title"] = _("Protocolos Pendientes de Orden de Trabajo")

        # Group protocols by veterinarian for easier processing
        protocols_by_vet = {}
        for protocol in context["protocols"]:
            vet_key = protocol.veterinarian.id
            if vet_key not in protocols_by_vet:
                protocols_by_vet[vet_key] = {
                    "veterinarian": protocol.veterinarian,
                    "protocols": [],
                }
            protocols_by_vet[vet_key]["protocols"].append(protocol)

        context["protocols_by_vet"] = protocols_by_vet.values()
        return context


class WorkOrderSelectProtocolsView(WorkOrderStaffRequiredMixin, View):
    """
    Select protocols for work order generation.
    """

    def get(self, request, *args, **kwargs):
        """Display protocol selection form."""
        from accounts.models import Veterinarian

        veterinarian_id = self.kwargs.get("veterinarian_id")
        veterinarian = get_object_or_404(Veterinarian, pk=veterinarian_id)

        protocols = Protocol.objects.filter(
            veterinarian=veterinarian,
            status=Protocol.Status.READY,
            work_order__isnull=True,
        ).select_related(
            "veterinarian__user",
            "cytology_sample",
            "histopathology_sample",
        )

        form = ProtocolSelectionForm(veterinarian=veterinarian)

        context = {
            "form": form,
            "protocols": protocols,
            "veterinarian": veterinarian,
            "title": _("Seleccionar Protocolos para Orden de Trabajo"),
        }

        return render(
            request, "protocols/workorder/select_protocols.html", context
        )

    def post(self, request, *args, **kwargs):
        """Process protocol selection."""
        from accounts.models import Veterinarian

        veterinarian_id = self.kwargs.get("veterinarian_id")
        veterinarian = get_object_or_404(Veterinarian, pk=veterinarian_id)

        protocols = Protocol.objects.filter(
            veterinarian=veterinarian,
            status=Protocol.Status.READY,
            work_order__isnull=True,
        )

        form = ProtocolSelectionForm(request.POST, veterinarian=veterinarian)

        if form.is_valid():
            selected_protocols = form.cleaned_data["protocols"]
            if selected_protocols:
                protocol_ids = ",".join(str(p.id) for p in selected_protocols)
                return redirect(
                    "protocols:workorder_create_with_protocols",
                    protocol_ids=protocol_ids,
                )
            else:
                messages.error(
                    request, _("Debe seleccionar al menos un protocolo.")
                )

        context = {
            "form": form,
            "protocols": protocols,
            "veterinarian": veterinarian,
            "title": _("Seleccionar Protocolos para Orden de Trabajo"),
        }

        return render(
            request, "protocols/workorder/select_protocols.html", context
        )


class WorkOrderCreateView(WorkOrderStaffRequiredMixin, FormView):
    """
    Create a new work order for selected protocols with service integration.
    """

    form_class = WorkOrderCreateForm
    template_name = "protocols/workorder/create.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calculation_service = WorkOrderCalculationService()
        self.creation_service = WorkOrderCreationService()
        self.email_service = EmailNotificationService()

    def get_success_url(self):
        """Redirect to work order detail after creation."""
        return reverse(
            "protocols:workorder_detail", kwargs={"pk": self.workorder.pk}
        )

    def get(self, request, *args, **kwargs):
        """Handle GET request with early returns and validation."""
        protocols = self.get_protocols()

        # Early return for empty protocols
        if not protocols.exists():
            messages.error(request, _("No se encontraron protocolos válidos."))
            return redirect("protocols:workorder_pending_protocols")

        # Early return for validation errors
        is_valid, error_message = (
            self.creation_service.validate_protocols_for_work_order(protocols)
        )
        if not is_valid:
            messages.error(request, error_message)
            return redirect("protocols:workorder_pending_protocols")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add protocols, veterinarian, and services_data to context."""
        context = super().get_context_data(**kwargs)
        protocols = self.get_protocols()
        context["protocols"] = protocols
        context["veterinarian"] = (
            protocols.first().veterinarian if protocols.exists() else None
        )
        context["services_data"] = self.calculation_service.calculate_services(
            protocols
        )
        context["title"] = _("Crear Orden de Trabajo")
        return context

    def get_protocols(self):
        """Get the protocols for this work order."""
        protocol_ids = self.kwargs["protocol_ids"].split(",")
        return Protocol.objects.filter(
            id__in=protocol_ids,
            status=Protocol.Status.READY,
        ).select_related(
            "veterinarian__user",
            "cytology_sample",
            "histopathology_sample",
        )

    def form_valid(self, form):
        """Create the work order with service integration."""
        protocols = self.get_protocols()

        # Early return for empty protocols
        if not protocols.exists():
            messages.error(
                self.request, _("No se encontraron protocolos válidos.")
            )
            return redirect("protocols:workorder_pending_protocols")

        # Create work order with services using service
        services_data = self.calculation_service.calculate_services(protocols)
        workorder = self.creation_service.create_work_order_with_services(
            form=form,
            protocols=protocols,
            services_data=services_data,
            created_by=self.request.user,
        )

        self.workorder = workorder

        messages.success(
            self.request, _("Orden de trabajo creada exitosamente.")
        )

        return super().form_valid(form)


class WorkOrderDetailView(WorkOrderStaffRequiredMixin, DetailView):
    """
    View work order details.
    """

    model = WorkOrder
    template_name = "protocols/workorder/detail.html"
    context_object_name = "work_order"

    def get_queryset(self):
        """Get work order with related objects."""
        return WorkOrder.objects.select_related(
            "veterinarian__user",
            "created_by",
        ).prefetch_related(
            "protocols__veterinarian__user",
            "protocols__cytology_sample",
            "protocols__histopathology_sample",
            "services__protocol",
        )

    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context["title"] = _("Detalle de Orden de Trabajo")
        return context


class WorkOrderIssueView(WorkOrderStaffRequiredMixin, View):
    """
    Issue a work order (mark as issued).
    """

    def post(self, request, *args, **kwargs):
        """Issue the work order."""
        workorder = get_object_or_404(WorkOrder, pk=self.kwargs["pk"])

        if workorder.status != WorkOrder.Status.DRAFT:
            messages.error(
                request,
                _("Solo se pueden emitir órdenes de trabajo en borrador."),
            )
            return redirect("protocols:workorder_detail", pk=workorder.pk)

        # Issue the work order
        workorder.issue()

        messages.success(request, _("Orden de trabajo emitida exitosamente."))

        return redirect("protocols:workorder_detail", pk=workorder.pk)


class WorkOrderSendView(WorkOrderStaffRequiredMixin, View):
    """
    Send a work order to the veterinarian.
    """

    def post(self, request, *args, **kwargs):
        """Send the work order."""
        workorder = get_object_or_404(WorkOrder, pk=self.kwargs["pk"])

        if workorder.status not in [
            WorkOrder.Status.DRAFT,
            WorkOrder.Status.ISSUED,
        ]:
            messages.error(
                request,
                _(
                    "Solo las órdenes en borrador o emitidas pueden ser enviadas."
                ),
            )
            return redirect("protocols:workorder_detail", pk=workorder.pk)

        # Send the work order
        try:
            workorder.mark_as_sent()
            send_work_order_notification(workorder)
            messages.success(
                request, _("Orden de trabajo enviada exitosamente.")
            )
        except Exception as e:
            messages.error(
                request,
                _("Error al enviar orden de trabajo: %(error)s")
                % {"error": str(e)},
            )

        return redirect("protocols:workorder_detail", pk=workorder.pk)


class WorkOrderPDFView(WorkOrderStaffRequiredMixin, View):
    """
    Generate PDF version of a work order with service integration.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pdf_service = PDFGenerationService()

    def get(self, request, *args, **kwargs):
        """Generate and return PDF work order using service."""
        workorder = get_object_or_404(WorkOrder, pk=self.kwargs["pk"])

        # Generate PDF using service
        pdf_buffer = self.pdf_service.generate_workorder_pdf(workorder)

        filename = f"orden_trabajo_{workorder.id}.pdf"
        response = HttpResponse(
            pdf_buffer.getvalue(), content_type="application/pdf"
        )
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response


# =============================================================================
# FUNCTION-BASED VIEWS (TO BE REFACTORED)
