import logging
from datetime import date
from io import BytesIO

import qrcode
from django.contrib import messages
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from accounts.mixins import (
    ProtocolOwnerOrStaffMixin,
    StaffRequiredMixin,
    VeterinarianProfileRequiredMixin,
    VeterinarianRequiredMixin,
)
from accounts.models import Veterinarian
from protocols.forms import (
    CytologyProtocolForm,
    HistopathologyProtocolForm,
    ProtocolEditForm,
    ReceptionForm,
    ReceptionSearchForm,
)
from protocols.models import (
    Cassette,
    CassetteSlide,
    ProcessingLog,
    Protocol,
    ProtocolStatusHistory,
    Slide,
)
from protocols.services.email_service import EmailNotificationService
from protocols.services.protocol_service import (
    ProtocolProcessingService,
    ProtocolReceptionService,
)

logger = logging.getLogger(__name__)

# ============================================================================
# CLASS-BASED VIEWS
# ============================================================================


class ProtocolListView(ListView):
    """
    Display list of protocols for the current user.
    Admin users see all protocols, veterinarians see only their own.
    Supports filtering by status, type, and date range.
    """

    model = Protocol
    template_name = "protocols/protocol_list.html"
    context_object_name = "protocols"
    paginate_by = 20

    def get_queryset(self):
        """Get protocols based on user permissions."""
        # Check access permissions
        if self.request.user.is_admin_user or self.request.user.is_staff:
            # Admin and staff users can see all protocols
            protocols = (
                Protocol.objects.all()
                .select_related("veterinarian")
                .prefetch_related("cytology_sample", "histopathology_sample")
            )
        else:
            # Non-admin users must be veterinarians and see only their own protocols
            # Middleware ensures veterinarian profile exists
            veterinarian = self.request.user.veterinarian_profile

            # Get all protocols for this veterinarian
            protocols = (
                Protocol.objects.filter(veterinarian=veterinarian)
                .select_related("veterinarian")
                .prefetch_related("cytology_sample", "histopathology_sample")
            )

        # Apply filters
        status_filter = self.request.GET.get("status")
        if status_filter:
            protocols = protocols.filter(status=status_filter)

        type_filter = self.request.GET.get("type")
        if type_filter:
            protocols = protocols.filter(analysis_type=type_filter)

        date_from = self.request.GET.get("date_from")
        if date_from:
            protocols = protocols.filter(submission_date__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            protocols = protocols.filter(submission_date__lte=date_to)

        search_query = self.request.GET.get("search")
        if search_query:
            protocols = protocols.filter(
                Q(animal_identification__icontains=search_query)
                | Q(temporary_code__icontains=search_query)
                | Q(protocol_number__icontains=search_query)
                | Q(presumptive_diagnosis__icontains=search_query)
            )

        return protocols

    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)

        # Get current filter values
        status_filter = self.request.GET.get("status")
        type_filter = self.request.GET.get("type")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        search_query = self.request.GET.get("search")

        # Prepare filter fields for the UI component
        filter_fields = [
            {
                "name": "search",
                "label": "Buscar",
                "type": "text",
                "placeholder": "Animal, código, diagnóstico...",
                "value": search_query,
            },
            {
                "name": "status",
                "label": "Estado",
                "type": "select",
                "placeholder": "Todos los estados",
                "choices": Protocol.Status.choices,
                "value": status_filter,
            },
            {
                "name": "type",
                "label": "Tipo",
                "type": "select",
                "placeholder": "Todos los tipos",
                "choices": Protocol.AnalysisType.choices,
                "value": type_filter,
            },
            {
                "name": "date_from",
                "label": "Desde",
                "type": "date",
                "value": date_from,
            },
            {
                "name": "date_to",
                "label": "Hasta",
                "type": "date",
                "value": date_to,
            },
        ]

        context.update(
            {
                "filter_fields": filter_fields,
                "status_choices": Protocol.Status.choices,
                "type_choices": Protocol.AnalysisType.choices,
                "is_admin_user": self.request.user.is_admin_user,
                "current_filters": {
                    "status": status_filter,
                    "type": type_filter,
                    "date_from": date_from,
                    "date_to": date_to,
                    "search": search_query,
                },
            }
        )

        return context

    def dispatch(self, request, *args, **kwargs):
        """Handle permission checks and redirects."""
        if not request.user.is_authenticated:
            return redirect("accounts:login")

        return super().dispatch(request, *args, **kwargs)


class ProtocolDetailView(ProtocolOwnerOrStaffMixin, DetailView):
    """
    Display detailed information about a specific protocol.
    """

    model = Protocol
    template_name = "protocols/protocol_detail.html"
    context_object_name = "protocol"

    def get_queryset(self):
        """Get protocol with related objects."""
        return Protocol.objects.select_related(
            "veterinarian__user",
            "cytology_sample",
            "histopathology_sample",
        ).prefetch_related(
            "status_history",
            "reception_logs",
            "processing_logs",
        )


class ProtocolPublicDetailView(DetailView):
    """
    Display protocol details for public access using external ID.
    No authentication required.
    """

    model = Protocol
    template_name = "protocols/protocol_public_detail.html"
    context_object_name = "protocol"
    slug_field = "external_id"
    slug_url_kwarg = "external_id"

    def get_queryset(self):
        """Get protocol with related objects."""
        return Protocol.objects.select_related(
            "veterinarian__user",
            "cytology_sample",
            "histopathology_sample",
        )


class ProtocolCreateCytologyView(VeterinarianProfileRequiredMixin, CreateView):
    """
    Create a new cytology protocol.
    """

    form_class = CytologyProtocolForm
    template_name = "protocols/protocol_form.html"

    def get_form_kwargs(self):
        """Get form kwargs, excluding instance for non-ModelForm."""
        kwargs = super().get_form_kwargs()
        kwargs.pop("instance", None)  # Remove instance for forms.Form
        return kwargs

    def get_success_url(self):
        """Redirect to protocol detail after successful creation."""
        return reverse(
            "protocols:protocol_detail", kwargs={"pk": self.object.pk}
        )

    def form_valid(self, form):
        """Save the protocol with the current veterinarian."""
        # Middleware ensures veterinarian profile exists
        veterinarian = self.request.user.veterinarian_profile

        self.object = form.save(veterinarian=veterinarian)
        messages.success(
            self.request,
            _(
                "Protocolo de citología creado exitosamente. Puede enviarlo cuando esté listo."
            ),
        )
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        """Add analysis type to context."""
        context = super().get_context_data(**kwargs)
        context["analysis_type"] = "cytology"
        return context


class ProtocolCreateHistopathologyView(
    VeterinarianProfileRequiredMixin, CreateView
):
    """
    Create a new histopathology protocol.
    """

    form_class = HistopathologyProtocolForm
    template_name = "protocols/protocol_form.html"

    def get_form_kwargs(self):
        """Get form kwargs, excluding instance for non-ModelForm."""
        kwargs = super().get_form_kwargs()
        kwargs.pop("instance", None)  # Remove instance for forms.Form
        return kwargs

    def get_success_url(self):
        """Redirect to protocol detail after successful creation."""
        return reverse(
            "protocols:protocol_detail", kwargs={"pk": self.object.pk}
        )

    def form_valid(self, form):
        """Save the protocol with the current veterinarian."""
        # Middleware ensures veterinarian profile exists
        veterinarian = self.request.user.veterinarian_profile

        self.object = form.save(veterinarian=veterinarian)
        messages.success(
            self.request,
            _(
                "Protocolo de histopatología creado exitosamente. Puede enviarlo cuando esté listo."
            ),
        )
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        """Add analysis type to context."""
        context = super().get_context_data(**kwargs)
        context["analysis_type"] = "histopathology"
        return context


class ProtocolEditView(ProtocolOwnerOrStaffMixin, UpdateView):
    """
    Edit an existing protocol.
    """

    model = Protocol
    form_class = ProtocolEditForm
    template_name = "protocols/protocol_edit.html"

    def dispatch(self, request, *args, **kwargs):
        """Check if protocol can be edited before processing the request."""
        self.object = self.get_object()

        # Check if protocol is editable - only draft protocols can be edited
        if not self.object.is_editable:
            messages.warning(
                request, _("Solo los protocolos en borrador pueden ser editados.")
            )
            return redirect("protocols:protocol_detail", pk=self.object.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add protocol and sample forms to context."""
        context = super().get_context_data(**kwargs)
        protocol = self.object
        
        # Add protocol form as protocol_form for template compatibility
        context['protocol_form'] = context['form']
        
        # Add sample form based on analysis type
        if protocol.analysis_type == Protocol.AnalysisType.CYTOLOGY:
            from protocols.forms import CytologySampleEditForm
            try:
                sample = protocol.cytology_sample
                context['sample_form'] = CytologySampleEditForm(instance=sample)
            except protocol.cytology_sample.RelatedObjectDoesNotExist:
                context['sample_form'] = CytologySampleEditForm()
        else:  # HISTOPATHOLOGY
            from protocols.forms import HistopathologySampleEditForm
            try:
                sample = protocol.histopathology_sample
                context['sample_form'] = HistopathologySampleEditForm(instance=sample)
            except protocol.histopathology_sample.RelatedObjectDoesNotExist:
                context['sample_form'] = HistopathologySampleEditForm()
        
        # Add analysis type for template
        context['analysis_type'] = protocol.analysis_type
        
        return context

    def get_success_url(self):
        """Redirect to protocol detail after successful update."""
        return reverse(
            "protocols:protocol_detail", kwargs={"pk": self.object.pk}
        )

    def form_valid(self, form):
        """Save the protocol and show success message."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            _("Protocolo actualizado exitosamente."),
        )
        return response


class ProtocolDeleteView(ProtocolOwnerOrStaffMixin, DeleteView):
    """
    Delete a protocol.
    """

    model = Protocol
    template_name = "protocols/protocol_confirm_delete.html"

    def get_success_url(self):
        """Redirect to protocol list after successful deletion."""
        return reverse("protocols:protocol_list")

    def delete(self, request, *args, **kwargs):
        """Delete the protocol and show success message."""
        response = super().delete(request, *args, **kwargs)
        messages.success(
            self.request,
            _("Protocolo eliminado exitosamente."),
        )
        return response


class ReceptionSearchView(StaffRequiredMixin, FormView):
    """
    Search for a protocol by temporary code for reception.
    """

    form_class = ReceptionSearchForm
    template_name = "protocols/reception_search.html"

    def get_context_data(self, **kwargs):
        """Add protocol to context if found."""
        context = super().get_context_data(**kwargs)
        context["protocol"] = getattr(self, "protocol", None)
        return context

    def form_valid(self, form):
        """Handle form submission and search for protocol with early returns."""
        temporary_code = form.cleaned_data["temporary_code"]

        try:
            protocol = Protocol.objects.select_related(
                "veterinarian__user",
                "cytology_sample",
                "histopathology_sample",
            ).get(temporary_code=temporary_code)
        except Protocol.DoesNotExist:
            messages.error(
                self.request,
                _("No se encontró ningún protocolo con el código %(code)s")
                % {"code": temporary_code},
            )
            return self.form_invalid(form)

        if protocol.status == Protocol.Status.DRAFT:
            messages.warning(
                self.request,
                _("Este protocolo aún está en borrador y no ha sido enviado."),
            )
            self.protocol = protocol
            return self.form_invalid(form)

        if protocol.status == Protocol.Status.RECEIVED:
            messages.info(
                self.request,
                _(
                    "Este protocolo ya fue recibido el %(date)s. Número: %(number)s"
                )
                % {
                    "date": protocol.reception_date.strftime("%d/%m/%Y"),
                    "number": protocol.protocol_number,
                },
            )
            self.protocol = protocol
            return self.form_invalid(form)

        # Protocol is ready for reception - redirect to confirmation
        return redirect("protocols:reception_confirm", pk=protocol.pk)


class ReceptionPendingView(StaffRequiredMixin, ListView):
    """
    Display list of protocols pending reception.
    """

    model = Protocol
    template_name = "protocols/reception_pending.html"
    context_object_name = "protocols"

    def get_queryset(self):
        """Get protocols pending reception."""
        protocols = (
            Protocol.objects.filter(status=Protocol.Status.SUBMITTED)
            .select_related(
                "veterinarian__user",
                "cytology_sample",
                "histopathology_sample",
            )
            .order_by("submission_date")
        )

        # Calculate days pending for each protocol
        for protocol in protocols:
            days_pending = (date.today() - protocol.submission_date).days
            protocol.days_pending = days_pending

        return protocols


class ReceptionHistoryView(StaffRequiredMixin, ListView):
    """
    Display list of received protocols.
    """

    model = Protocol
    template_name = "protocols/reception_history.html"
    context_object_name = "protocols"
    paginate_by = 20

    def get_queryset(self):
        """Get received protocols."""
        return (
            Protocol.objects.filter(
                status__in=[
                    Protocol.Status.RECEIVED,
                    Protocol.Status.PROCESSING,
                    Protocol.Status.READY,
                    Protocol.Status.REPORT_SENT,
                ]
            )
            .select_related(
                "veterinarian__user",
                "cytology_sample",
                "histopathology_sample",
            )
            .order_by("-reception_date")
        )


class ProtocolSubmitView(ProtocolOwnerOrStaffMixin, View):
    """
    Submit a draft protocol.
    Generates temporary code and changes status to SUBMITTED.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email_service = EmailNotificationService()

    def post(self, request, *args, **kwargs):
        """Handle protocol submission with service integration."""
        protocol = self.get_object()

        try:
            protocol.submit()

            # Log status change
            ProtocolStatusHistory.log_status_change(
                protocol=protocol,
                new_status=Protocol.Status.SUBMITTED,
                changed_by=request.user,
                description="Protocol submitted by veterinarian",
            )

            # Send submission confirmation email using service
            self.email_service.send_submission_confirmation_email(protocol)

            messages.success(
                request,
                _(
                    "¡Protocolo enviado exitosamente! Código temporal: %(code)s. Por favor incluya este código con su muestra."
                )
                % {"code": protocol.temporary_code},
            )
        except ValueError as e:
            messages.error(request, str(e))

        return redirect("protocols:protocol_detail", pk=protocol.pk)

    def get_object(self):
        """Get the protocol object."""
        return get_object_or_404(Protocol, pk=self.kwargs["pk"])


class ReceptionDetailView(StaffRequiredMixin, DetailView):
    """
    Show reception confirmation and label printing options.
    """

    model = Protocol
    template_name = "protocols/reception_detail.html"
    context_object_name = "protocol"

    def get_queryset(self):
        """Get protocol with related objects."""
        return Protocol.objects.select_related(
            "veterinarian__user",
            "cytology_sample",
            "histopathology_sample",
        )


class ProcessingDashboardView(StaffRequiredMixin, TemplateView):
    """
    Display processing dashboard with statistics and queue information.
    """

    template_name = "protocols/processing/dashboard.html"

    def get_context_data(self, **kwargs):
        """Add processing statistics to context."""
        context = super().get_context_data(**kwargs)

        # Get received protocols that need processing
        protocols_received = (
            Protocol.objects.filter(status=Protocol.Status.RECEIVED)
            .select_related(
                "veterinarian__user",
                "cytology_sample",
                "histopathology_sample",
            )
            .count()
        )

        # Get protocols currently in processing
        protocols_processing = (
            Protocol.objects.filter(status=Protocol.Status.PROCESSING)
            .select_related(
                "veterinarian__user",
                "cytology_sample",
                "histopathology_sample",
            )
            .count()
        )

        # Get protocols ready for analysis
        protocols_ready = Protocol.objects.filter(
            status=Protocol.Status.READY
        ).count()

        # Get cassettes by status
        cassettes_pending = Cassette.objects.filter(
            estado=Cassette.Status.PENDIENTE
        ).count()
        cassettes_processing = Cassette.objects.filter(
            estado=Cassette.Status.EN_PROCESO
        ).count()
        cassettes_completed = Cassette.objects.filter(
            estado=Cassette.Status.COMPLETADO
        ).count()

        # Get slides by status
        slides_pending = Slide.objects.filter(
            estado=Slide.Status.PENDIENTE
        ).count()
        slides_mounted = Slide.objects.filter(
            estado=Slide.Status.MONTADO
        ).count()
        slides_stained = Slide.objects.filter(
            estado=Slide.Status.COLOREADO
        ).count()
        slides_ready = Slide.objects.filter(estado=Slide.Status.LISTO).count()

        # Recent processing activity
        recent_logs = ProcessingLog.objects.select_related(
            "protocol",
            "cassette",
            "slide",
            "usuario",
        ).order_by("-created_at")[:10]

        context.update(
            {
                "protocols_received": protocols_received,
                "protocols_processing": protocols_processing,
                "protocols_ready": protocols_ready,
                "cassettes_pending": cassettes_pending,
                "cassettes_processing": cassettes_processing,
                "cassettes_completed": cassettes_completed,
                "slides_pending": slides_pending,
                "slides_mounted": slides_mounted,
                "slides_stained": slides_stained,
                "slides_ready": slides_ready,
                "recent_logs": recent_logs,
            }
        )

        return context


class ProcessingQueueView(StaffRequiredMixin, ListView):
    """
    Display processing queue with protocols ready for processing.
    """

    model = Protocol
    template_name = "protocols/processing/queue.html"
    context_object_name = "protocols"
    paginate_by = 20

    def get_queryset(self):
        """Get protocols in processing queue with filtering."""
        # Get filter parameters
        analysis_type = self.request.GET.get("type", "all")

        # Base queryset - received and processing protocols
        protocols = (
            Protocol.objects.filter(
                status__in=[
                    Protocol.Status.RECEIVED,
                    Protocol.Status.PROCESSING,
                ]
            )
            .select_related(
                "veterinarian__user",
                "cytology_sample",
                "histopathology_sample",
            )
            .order_by("reception_date")
        )

        # Apply type filter
        if analysis_type != "all":
            protocols = protocols.filter(analysis_type=analysis_type)

        # Calculate processing info
        for protocol in protocols:
            days_in_process = (
                (date.today() - protocol.reception_date.date()).days
                if protocol.reception_date
                else 0
            )
            protocol.days_in_process = days_in_process

            # Check what's pending
            if protocol.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY:
                cassettes = (
                    protocol.histopathology_sample.cassettes.all()
                    if hasattr(protocol, "histopathology_sample")
                    else []
                )
                protocol.cassettes_count = len(cassettes)
                protocol.cassettes_completed = sum(
                    1
                    for c in cassettes
                    if c.estado == Cassette.Status.COMPLETADO
                )
            else:
                protocol.cassettes_count = 0
                protocol.cassettes_completed = 0

        return protocols

    def get_context_data(self, **kwargs):
        """Add filter context."""
        context = super().get_context_data(**kwargs)

        # Get current filter values
        analysis_type = self.request.GET.get("type", "all")

        # Prepare filter fields for the UI component
        filter_fields = [
            {
                "name": "type",
                "label": "Tipo",
                "type": "select",
                "placeholder": "Todos los tipos",
                "choices": [
                    ("all", "Todos"),
                    ("cytology", "Citología"),
                    ("histopathology", "Histopatología"),
                ],
                "value": analysis_type,
            },
        ]

        context.update(
            {
                "filter_fields": filter_fields,
                "current_filters": {
                    "type": analysis_type,
                },
            }
        )

        return context


class ProtocolProcessingStatusView(StaffRequiredMixin, DetailView):
    """
    Show complete processing status for a protocol with timeline.
    """

    model = Protocol
    template_name = "protocols/processing/protocol_status.html"
    context_object_name = "protocol"

    def get_queryset(self):
        """Get protocol with related objects."""
        return Protocol.objects.select_related(
            "veterinarian__user",
            "cytology_sample",
            "histopathology_sample",
        )

    def get_context_data(self, **kwargs):
        """Add processing-related context data."""
        context = super().get_context_data(**kwargs)
        protocol = self.object

        # Get cassettes for histopathology
        cassettes = []
        if (
            protocol.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY
            and hasattr(protocol, "histopathology_sample")
        ):
            cassettes = protocol.histopathology_sample.cassettes.all().prefetch_related(
                "cassette_slides__slide"
            )

        # Get slides
        slides = protocol.slides.all().prefetch_related(
            "cassette_slides__cassette"
        )

        # Get processing logs
        processing_logs = (
            ProcessingLog.objects.filter(protocol=protocol)
            .select_related("usuario", "cassette", "slide")
            .order_by("created_at")
        )

        # Get status history
        status_history = protocol.status_history.all().select_related(
            "changed_by"
        )

        context.update(
            {
                "cassettes": cassettes,
                "slides": slides,
                "processing_logs": processing_logs,
                "status_history": status_history,
            }
        )

        return context


class CassetteCreateView(StaffRequiredMixin, View):
    """
    Create cassettes for a histopathology protocol.
    """

    def get(self, request, *args, **kwargs):
        """Show cassette creation form."""
        protocol = self.get_protocol()

        if protocol is None:
            # Redirect to processing status if validation failed
            return redirect(
                "protocols:processing_status", pk=self.kwargs["protocol_pk"]
            )

        # Get existing cassettes
        existing_cassettes = protocol.histopathology_sample.cassettes.all()

        context = {
            "protocol": protocol,
            "existing_cassettes": existing_cassettes,
        }
        return render(
            request, "protocols/processing/cassette_create.html", context
        )

    def post(self, request, *args, **kwargs):
        """Create cassettes."""
        protocol = self.get_protocol()

        if protocol is None:
            # Redirect to processing status if validation failed
            return redirect(
                "protocols:processing_status", pk=self.kwargs["protocol_pk"]
            )

        try:
            # Get form data
            cassette_count = int(request.POST.get("cassette_count", 1))
            if cassette_count < 1 or cassette_count > 20:
                raise ValueError("Invalid cassette count")

            # Create cassettes with form data
            created_cassettes = []
            for i in range(cassette_count):
                # Get cassette-specific data
                material = request.POST.get(f"material_{i}", "")
                tipo = request.POST.get(
                    f"tipo_{i}", Cassette.CassetteType.NORMAL
                )
                color = request.POST.get(
                    f"color_{i}", Cassette.CassetteColor.BLANCO
                )
                observaciones = request.POST.get(f"observaciones_{i}", "")

                cassette = Cassette.objects.create(
                    histopathology_sample=protocol.histopathology_sample,
                    material_incluido=material,
                    tipo_cassette=tipo,
                    color_cassette=color,
                    observaciones=observaciones,
                )

                # Update to encasetado stage
                cassette.update_stage("encasetado")

                # Log action
                ProcessingLog.log_action(
                    protocol=protocol,
                    etapa=ProcessingLog.Stage.ENCASETADO,
                    usuario=request.user,
                    cassette=cassette,
                    observaciones=f"Cassette creado: {material[:50]}",
                )

                created_cassettes.append(cassette)

            # Update protocol status to processing
            if protocol.status == Protocol.Status.RECEIVED:
                protocol.status = Protocol.Status.PROCESSING
                protocol.save(update_fields=["status"])

                ProtocolStatusHistory.log_status_change(
                    protocol=protocol,
                    new_status=Protocol.Status.PROCESSING,
                    changed_by=request.user,
                    description=f"Iniciado procesamiento - {len(created_cassettes)} cassettes creados",
                )

            messages.success(
                request,
                _(
                    f"Se crearon {len(created_cassettes)} cassettes exitosamente."
                ),
            )

        except (ValueError, TypeError) as e:
            messages.error(
                request,
                _("Error al crear cassettes: %(error)s") % {"error": str(e)},
            )

        return redirect("protocols:slide_register", protocol_pk=protocol.pk)

    def get_protocol(self):
        """Get and validate protocol."""
        protocol = get_object_or_404(
            Protocol.objects.select_related("histopathology_sample"),
            pk=self.kwargs["protocol_pk"],
        )

        # Verify it's histopathology
        if protocol.analysis_type != Protocol.AnalysisType.HISTOPATHOLOGY:
            messages.error(
                self.request,
                _(
                    "Solo los protocolos de histopatología requieren cassettes."
                ),
            )
            return None

        if not hasattr(protocol, "histopathology_sample"):
            messages.error(
                self.request,
                _("Este protocolo no tiene muestra de histopatología."),
            )
            return None

        return protocol


class ReceptionConfirmView(StaffRequiredMixin, FormView):
    """
    Confirm reception of a protocol and assign final protocol number.
    """

    form_class = ReceptionForm
    template_name = "protocols/reception_confirm.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reception_service = ProtocolReceptionService()
        self.email_service = EmailNotificationService()

    def get_success_url(self):
        """Redirect to reception detail after successful confirmation."""
        return reverse(
            "protocols:reception_detail", kwargs={"pk": self.kwargs["pk"]}
        )

    def get(self, request, *args, **kwargs):
        """Handle GET request with protocol validation."""
        protocol = self.get_protocol()
        if protocol is None:
            return redirect("protocols:reception_search")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add protocol to context."""
        context = super().get_context_data(**kwargs)
        context["protocol"] = self.get_protocol()
        return context

    def get_protocol(self):
        """Get and validate protocol."""
        protocol = get_object_or_404(
            Protocol.objects.select_related(
                "veterinarian__user",
                "cytology_sample",
                "histopathology_sample",
            ),
            pk=self.kwargs["pk"],
        )

        # Early return for invalid protocol status
        is_valid, error_message = (
            self.reception_service.validate_protocol_for_reception(protocol)
        )
        if not is_valid:
            messages.warning(self.request, error_message)
            return None

        return protocol

    def form_valid(self, form):
        """Process reception confirmation with early returns and service integration."""
        protocol = self.get_protocol()
        if protocol is None:
            return redirect("protocols:reception_search")

        # Process reception using service
        form_data = form.cleaned_data
        success, error_message = self.reception_service.process_reception(
            protocol, form_data, self.request.user
        )

        if not success:
            messages.error(
                self.request, f"Error al procesar recepción: {error_message}"
            )
            return redirect("protocols:reception_search")

        # Send email notifications using service
        self.email_service.send_reception_email(protocol)

        # Send discrepancy alert if issues found
        discrepancies = form_data.get("discrepancies", "")
        if discrepancies:
            sample_condition = form_data.get("sample_condition", "")
            self.email_service.send_discrepancy_alert_email(
                protocol, discrepancies, sample_condition
            )

        messages.success(
            self.request,
            _("Muestra recibida exitosamente. Protocolo: %(number)s")
            % {"number": protocol.protocol_number},
        )

        return redirect(self.get_success_url())


class ProtocolSelectTypeView(VeterinarianRequiredMixin, TemplateView):
    """
    Show a page to select the type of protocol to create.
    """

    template_name = "protocols/protocol_select_type.html"


class ReceptionLabelPDFView(StaffRequiredMixin, View):
    """
    Generate printable labels for a received sample.
    Returns a PDF with QR code and protocol information for 39x20mm tickets.
    """

    def get(self, request, *args, **kwargs):
        """Generate PDF label."""
        protocol = self.get_protocol()

        if protocol is None:
            return redirect("protocols:reception_search")

        # 39x20 mm ticket paper configuration
        page_width = 39 * mm
        page_height = 20 * mm

        # Create PDF buffer
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=(page_width, page_height))

        # Generate QR code
        qr_data = f"PROTOCOLO:{protocol.protocol_number}"
        qr = qrcode.QRCode(version=1, box_size=2, border=1)
        qr.add_data(qr_data)
        qr.make()

        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        qr_image.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        qr_image_reader = ImageReader(qr_buffer)

        # QR code size (small for 39x20mm)
        qr_size = 12 * mm
        qr_x = 1 * mm
        qr_y = 4 * mm

        # Text area
        text_x = qr_x + qr_size + 1 * mm

        # Protocol number (top line)
        protocol_text = (
            protocol.protocol_number[:8]
            if len(protocol.protocol_number) > 8
            else protocol.protocol_number
        )
        p.drawString(text_x, qr_y + qr_size - 3 * mm, protocol_text)

        # Animal ID (second line)
        animal_text = (
            protocol.animal_identification[:10]
            if len(protocol.animal_identification) > 10
            else protocol.animal_identification
        )
        p.drawString(text_x, qr_y + qr_size - 6 * mm, animal_text)

        # Species (third line)
        species_text = (
            protocol.species[:8]
            if len(protocol.species) > 8
            else protocol.species
        )
        p.drawString(text_x, qr_y + qr_size - 9 * mm, species_text)

        # Analysis type (bottom line)
        analysis_type = (
            "CT"
            if protocol.analysis_type == Protocol.AnalysisType.CYTOLOGY
            else "HP"
        )
        p.drawString(text_x, qr_y + 1 * mm, analysis_type)

        # Draw QR code
        p.drawImage(qr_image_reader, qr_x, qr_y, width=qr_size, height=qr_size)

        p.showPage()
        p.save()

        buffer.seek(0)
        filename = f"label_{protocol.protocol_number.replace(' ', '_')}.pdf"
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=filename,
        )

    def get_protocol(self):
        """Get and validate protocol."""
        protocol = get_object_or_404(
            Protocol.objects.select_related(
                "veterinarian__user",
                "cytology_sample",
                "histopathology_sample",
            ),
            pk=self.kwargs["pk"],
        )

        if not protocol.protocol_number:
            messages.error(
                self.request, _("Este protocolo aún no tiene número asignado.")
            )
            return None

        return protocol


class SlideRegisterView(StaffRequiredMixin, View):
    """
    Register slides for a protocol with interactive cassette-slide relationship.
    """

    def get(self, request, *args, **kwargs):
        """Show interactive slide registration interface."""
        protocol = self.get_protocol()

        if protocol is None:
            return redirect(
                "protocols:processing_status", pk=self.kwargs["protocol_pk"]
            )

        # Get existing cassettes (for histopathology)
        cassettes = []
        if (
            protocol.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY
            and hasattr(protocol, "histopathology_sample")
        ):
            cassettes = list(
                protocol.histopathology_sample.cassettes.all().order_by(
                    "codigo_cassette"
                )
            )

        # Get existing slides
        existing_slides = list(
            protocol.slides.all().prefetch_related("cassette_slides__cassette")
        )

        # Prepare existing relationships for the template
        existing_relationships = {}
        for slide in existing_slides:
            for cs in slide.cassette_slides.all():
                # Key format: "slide_number-position" (e.g., "1-1", "1-2")
                # Determine position based on order (simplified)
                position = (
                    1 if not existing_relationships.get(f"{slide.id}-1") else 2
                )
                key = f"{slide.id}-{position}"
                existing_relationships[key] = cs.cassette.id

        context = {
            "protocol": protocol,
            "cassettes": cassettes,
            "existing_slides": existing_slides,
            "existing_relationships": existing_relationships,
            "is_cytology": protocol.analysis_type
            == Protocol.AnalysisType.CYTOLOGY,
        }
        return render(
            request, "protocols/processing/slide_register.html", context
        )

    def post(self, request, *args, **kwargs):
        """Process slide registration."""
        protocol = self.get_protocol()

        if protocol is None:
            return redirect(
                "protocols:processing_status", pk=self.kwargs["protocol_pk"]
            )

        try:
            # Get form data
            slide_count = int(request.POST.get("slide_count", 1))
            if slide_count < 1 or slide_count > 50:
                raise ValueError("Invalid slide count")

            # Create slides
            created_slides = []
            for i in range(slide_count):
                # Get slide-specific data
                codigo_portaobjetos = request.POST.get(
                    f"codigo_portaobjetos_{i}", ""
                )
                campo = request.POST.get(f"campo_{i}")
                campo = int(campo) if campo else None
                tecnica_coloracion = request.POST.get(
                    f"tecnica_coloracion_{i}", ""
                )
                observaciones = request.POST.get(f"observaciones_{i}", "")

                # Create slide
                slide = Slide.objects.create(
                    protocol=protocol,
                    codigo_portaobjetos=codigo_portaobjetos,
                    campo=campo,
                    tecnica_coloracion=tecnica_coloracion,
                    observaciones=observaciones,
                    estado=Slide.Status.PENDIENTE,
                )

                # Handle cassette relationships for histopathology
                if (
                    protocol.analysis_type
                    == Protocol.AnalysisType.HISTOPATHOLOGY
                ):
                    # Get cassette relationships for this slide
                    for pos in [
                        1,
                        2,
                    ]:  # Each slide can have up to 2 cassette positions
                        cassette_id = request.POST.get(f"cassette_{i}_{pos}")
                        if cassette_id:
                            try:
                                cassette = Cassette.objects.get(
                                    id=cassette_id,
                                    histopathology_sample=protocol.histopathology_sample,
                                )
                                CassetteSlide.objects.create(
                                    cassette=cassette,
                                    slide=slide,
                                    position=pos,
                                )
                            except Cassette.DoesNotExist:
                                pass

                # Log action
                ProcessingLog.log_action(
                    protocol=protocol,
                    etapa=ProcessingLog.Stage.MONTAJE,
                    usuario=request.user,
                    slide=slide,
                    observaciones=f"Slide registrado: {codigo_portaobjetos}",
                )

                created_slides.append(slide)

            messages.success(
                request,
                _(
                    f"Se registraron {len(created_slides)} slides exitosamente."
                ),
            )

        except (ValueError, TypeError) as e:
            messages.error(
                request,
                _("Error al registrar slides: %(error)s") % {"error": str(e)},
            )

        return redirect("protocols:processing_status", pk=protocol.pk)

    def get_protocol(self):
        """Get and validate protocol."""
        protocol = get_object_or_404(
            Protocol.objects.select_related(
                "veterinarian__user",
                "cytology_sample",
                "histopathology_sample",
            ),
            pk=self.kwargs["protocol_pk"],
        )
        return protocol


class SlideUpdateStageView(StaffRequiredMixin, View):
    """
    Update slide processing stage (montaje, coloración, listo) with service integration.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processing_service = ProtocolProcessingService()

    def post(self, request, *args, **kwargs):
        """Update slide stage using service."""
        slide = get_object_or_404(Slide, pk=self.kwargs["slide_pk"])

        stage = request.POST.get("stage")
        observaciones = request.POST.get("observaciones", "")

        # Use service to update slide stage
        success, error_message = self.processing_service.update_slide_stage(
            slide, stage, request.user, observaciones
        )

        if success:
            messages.success(
                request,
                _(f"Slide {slide.codigo_portaobjetos} actualizado a {stage}."),
            )
        else:
            messages.error(request, error_message)

        return redirect("protocols:processing_status", pk=slide.protocol.pk)


class SlideUpdateQualityView(StaffRequiredMixin, View):
    """
    Update slide quality assessment with service integration.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processing_service = ProtocolProcessingService()

    def post(self, request, *args, **kwargs):
        """Update slide quality using service."""
        slide = get_object_or_404(Slide, pk=self.kwargs["slide_pk"])

        quality = request.POST.get("quality")
        observaciones = request.POST.get("observaciones", "")

        # Use service to update slide quality
        success, error_message = self.processing_service.update_slide_quality(
            slide, quality, observaciones
        )

        if success:
            messages.success(
                request,
                _(
                    f"Calidad de slide {slide.codigo_portaobjetos} actualizada."
                ),
            )
        else:
            messages.error(request, error_message)

        return redirect("protocols:processing_status", pk=slide.protocol.pk)
