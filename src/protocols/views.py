import logging
from datetime import date
from io import BytesIO

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from accounts.models import Veterinarian
from protocols.emails import (
    queue_email,
    send_sample_reception_notification,
)
from protocols.forms import (
    CytologyProtocolForm,
    CytologySampleEditForm,
    HistopathologyProtocolForm,
    HistopathologySampleEditForm,
    ProtocolEditForm,
    ReceptionForm,
    ReceptionSearchForm,
)
from protocols.models import (
    Cassette,
    CassetteSlide,
    EmailLog,
    ProcessingLog,
    Protocol,
    ProtocolStatusHistory,
    ReceptionLog,
    Slide,
)

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _send_reception_email(protocol):
    """
    Send reception confirmation email to veterinarian asynchronously.

    Uses Celery-based email system for non-blocking delivery with
    automatic retry logic and preference checking.

    Args:
        protocol: Protocol instance that was received

    Returns:
        bool: True if email was queued successfully, False otherwise
    """
    try:
        email_log = send_sample_reception_notification(protocol)
        if email_log:
            logger.info(
                f"Reception email queued for protocol {protocol.pk} "
                f"(EmailLog ID: {email_log.id})"
            )
            return True
        else:
            logger.info(
                f"Reception email skipped for protocol {protocol.pk} "
                "(veterinarian preferences)"
            )
            return False
    except Exception as e:
        logger.error(
            f"Failed to queue reception email for protocol {protocol.pk}: {e}"
        )
        return False


def _send_submission_confirmation_email(protocol):
    """
    Send protocol submission confirmation email to veterinarian.

    Args:
        protocol: Protocol instance that was submitted

    Returns:
        bool: True if email was queued successfully, False otherwise
    """
    try:
        email_log = queue_email(
            email_type=EmailLog.EmailType.CUSTOM,
            recipient_email=protocol.veterinarian.email,
            subject=f"Protocolo {protocol.temporary_code} enviado exitosamente",
            context={
                "protocol": protocol,
                "veterinarian": protocol.veterinarian,
            },
            template_name="emails/protocol_submitted.html",
            protocol=protocol,
            veterinarian=protocol.veterinarian,
        )
        logger.info(
            f"Submission email queued for protocol {protocol.pk} "
            f"(EmailLog ID: {email_log.id})"
        )
        return True
    except Exception as e:
        logger.error(
            f"Failed to queue submission email for protocol {protocol.pk}: {e}"
        )
        return False


def _send_discrepancy_alert_email(protocol, discrepancies, sample_condition):
    """
    Send discrepancy alert email when sample issues are found.

    Args:
        protocol: Protocol instance with discrepancies
        discrepancies: String describing the discrepancies found
        sample_condition: Sample condition value

    Returns:
        bool: True if email was queued successfully, False otherwise
    """
    try:
        email_log = queue_email(
            email_type=EmailLog.EmailType.CUSTOM,
            recipient_email=protocol.veterinarian.email,
            subject=f"Discrepancias encontradas - Protocolo {protocol.protocol_number}",
            context={
                "protocol": protocol,
                "veterinarian": protocol.veterinarian,
                "discrepancies": discrepancies,
                "sample_condition": protocol.get_sample_condition_display(),
            },
            template_name="emails/reception_discrepancies.html",
            protocol=protocol,
            veterinarian=protocol.veterinarian,
        )
        logger.info(
            f"Discrepancy alert queued for protocol {protocol.pk} "
            f"(EmailLog ID: {email_log.id})"
        )
        return True
    except Exception as e:
        logger.error(
            f"Failed to queue discrepancy email for protocol {protocol.pk}: {e}"
        )
        return False


# ============================================================================
# PROTOCOL VIEWS
# ============================================================================


@login_required
def protocol_list_view(request):
    """
    Display list of protocols for the current user.
    Admin users see all protocols, veterinarians see only their own.
    Supports filtering by status, type, and date range.
    """
    # Check access permissions
    if request.user.is_admin_user:
        # Admin users can see all protocols
        protocols = (
            Protocol.objects.all()
            .select_related("veterinarian")
            .prefetch_related("cytology_sample", "histopathology_sample")
        )
    else:
        # Non-admin users must be veterinarians and see only their own protocols
        try:
            veterinarian = request.user.veterinarian_profile
        except Veterinarian.DoesNotExist:
            messages.error(
                request, _("Debe completar su perfil de veterinario primero.")
            )
            return redirect("accounts:complete_profile")

        # Get all protocols for this veterinarian
        protocols = (
            Protocol.objects.filter(veterinarian=veterinarian)
            .select_related("veterinarian")
            .prefetch_related("cytology_sample", "histopathology_sample")
        )

    # Apply filters
    status_filter = request.GET.get("status")
    if status_filter:
        protocols = protocols.filter(status=status_filter)

    type_filter = request.GET.get("type")
    if type_filter:
        protocols = protocols.filter(analysis_type=type_filter)

    date_from = request.GET.get("date_from")
    if date_from:
        protocols = protocols.filter(submission_date__gte=date_from)

    date_to = request.GET.get("date_to")
    if date_to:
        protocols = protocols.filter(submission_date__lte=date_to)

    search_query = request.GET.get("search")
    if search_query:
        protocols = protocols.filter(
            Q(animal_identification__icontains=search_query)
            | Q(temporary_code__icontains=search_query)
            | Q(protocol_number__icontains=search_query)
            | Q(presumptive_diagnosis__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(protocols, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

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

    context = {
        "page_obj": page_obj,
        "protocols": protocols,  # For results count
        "filter_fields": filter_fields,
        "status_choices": Protocol.Status.choices,
        "type_choices": Protocol.AnalysisType.choices,
        "is_admin_user": request.user.is_admin_user,
        "current_filters": {
            "status": status_filter,
            "type": type_filter,
            "date_from": date_from,
            "date_to": date_to,
            "search": search_query,
        },
    }
    return render(request, "protocols/protocol_list.html", context)


def protocol_public_detail_view(request, external_id):
    """
    Display detailed information for a specific protocol using external UUID.
    This view is accessible without authentication for external sharing.
    """
    # Get protocol by external_id
    protocol = get_object_or_404(
        Protocol.objects.select_related("veterinarian").prefetch_related(
            "cytology_sample", "histopathology_sample", "status_history"
        ),
        external_id=external_id,
    )

    # Get status history
    status_history = protocol.status_history.all().select_related("changed_by")

    # Get sample details (use hasattr to avoid exceptions)
    sample = None
    if protocol.analysis_type == Protocol.AnalysisType.CYTOLOGY and hasattr(
        protocol, "cytology_sample"
    ):
        sample = protocol.cytology_sample
    elif hasattr(protocol, "histopathology_sample"):
        sample = protocol.histopathology_sample

    context = {
        "protocol": protocol,
        "sample": sample,
        "status_history": status_history,
        "is_public_view": True,  # Flag to indicate this is a public view
    }
    return render(request, "protocols/protocol_detail.html", context)


@login_required
def protocol_detail_view(request, pk):
    """
    Display detailed information for a specific protocol.
    """
    # Get protocol
    protocol = get_object_or_404(
        Protocol.objects.select_related("veterinarian").prefetch_related(
            "cytology_sample", "histopathology_sample", "status_history"
        ),
        pk=pk,
    )

    # Check access permissions
    if request.user.is_admin_user:
        # Admin users can see all protocols
        pass
    else:
        # Non-admin users must be veterinarians and own the protocol
        try:
            veterinarian = request.user.veterinarian_profile
        except Veterinarian.DoesNotExist:
            messages.error(
                request, _("Debe completar su perfil de veterinario primero.")
            )
            return redirect("accounts:complete_profile")

        if protocol.veterinarian != veterinarian:
            return HttpResponseForbidden(
                _("No tiene permiso para ver este protocolo.")
            )

    # Get status history
    status_history = protocol.status_history.all().select_related("changed_by")

    # Get sample details (use hasattr to avoid exceptions)
    sample = None
    if protocol.analysis_type == Protocol.AnalysisType.CYTOLOGY and hasattr(
        protocol, "cytology_sample"
    ):
        sample = protocol.cytology_sample
    elif hasattr(protocol, "histopathology_sample"):
        sample = protocol.histopathology_sample

    context = {
        "protocol": protocol,
        "sample": sample,
        "status_history": status_history,
    }
    return render(request, "protocols/protocol_detail.html", context)


@login_required
@csrf_protect
def protocol_create_cytology_view(request):
    """
    Create a new cytology protocol.
    """
    # Ensure user is a veterinarian
    try:
        veterinarian = request.user.veterinarian_profile
    except Veterinarian.DoesNotExist:
        messages.error(
            request, _("Debe completar su perfil de veterinario primero.")
        )
        return redirect("accounts:complete_profile")

    if request.method == "POST":
        form = CytologyProtocolForm(request.POST)
        if form.is_valid():
            protocol = form.save(veterinarian=veterinarian)
            messages.success(
                request,
                _(
                    "Protocolo de citología creado exitosamente. Puede enviarlo cuando esté listo."
                ),
            )
            return redirect("protocols:protocol_detail", pk=protocol.pk)
    else:
        form = CytologyProtocolForm()

    context = {
        "form": form,
        "analysis_type": "cytology",
    }
    return render(request, "protocols/protocol_form.html", context)


@login_required
@csrf_protect
def protocol_create_histopathology_view(request):
    """
    Create a new histopathology protocol.
    """
    # Ensure user is a veterinarian
    try:
        veterinarian = request.user.veterinarian_profile
    except Veterinarian.DoesNotExist:
        messages.error(
            request, _("Debe completar su perfil de veterinario primero.")
        )
        return redirect("accounts:complete_profile")

    if request.method == "POST":
        form = HistopathologyProtocolForm(request.POST)
        if form.is_valid():
            protocol = form.save(veterinarian=veterinarian)
            messages.success(
                request,
                _(
                    "Protocolo de histopatología creado exitosamente. Puede enviarlo cuando esté listo."
                ),
            )
            return redirect("protocols:protocol_detail", pk=protocol.pk)
    else:
        form = HistopathologyProtocolForm()

    context = {
        "form": form,
        "analysis_type": "histopathology",
    }
    return render(request, "protocols/protocol_form.html", context)


@login_required
@csrf_protect
def protocol_edit_view(request, pk):
    """
    Edit an existing protocol (only drafts can be edited).
    """
    # Ensure user is a veterinarian
    try:
        veterinarian = request.user.veterinarian_profile
    except Veterinarian.DoesNotExist:
        messages.error(
            request, _("Debe completar su perfil de veterinario primero.")
        )
        return redirect("accounts:complete_profile")

    # Get protocol and ensure it belongs to this veterinarian
    protocol = get_object_or_404(Protocol, pk=pk)

    if protocol.veterinarian != veterinarian:
        return HttpResponseForbidden(
            _("No tiene permiso para editar este protocolo.")
        )

    if not protocol.is_editable:
        messages.error(
            request, _("Solo los protocolos en borrador pueden ser editados.")
        )
        return redirect("protocols:protocol_detail", pk=protocol.pk)

    # Get appropriate sample based on analysis type
    is_cytology = protocol.analysis_type == Protocol.AnalysisType.CYTOLOGY
    sample = (
        protocol.cytology_sample
        if is_cytology
        else protocol.histopathology_sample
    )
    SampleFormClass = (
        CytologySampleEditForm if is_cytology else HistopathologySampleEditForm
    )

    # Handle POST request
    if request.method == "POST":
        protocol_form = ProtocolEditForm(request.POST, instance=protocol)
        sample_form = SampleFormClass(request.POST, instance=sample)

        if not (protocol_form.is_valid() and sample_form.is_valid()):
            # Forms invalid - render with errors
            context = {
                "protocol": protocol,
                "protocol_form": protocol_form,
                "sample_form": sample_form,
                "analysis_type": protocol.analysis_type,
            }
            return render(request, "protocols/protocol_edit.html", context)

        # Forms valid - save and redirect
        protocol_form.save()
        sample_form.save()
        messages.success(request, _("Protocolo actualizado exitosamente."))
        return redirect("protocols:protocol_detail", pk=protocol.pk)

    # GET request - show empty forms
    protocol_form = ProtocolEditForm(instance=protocol)
    sample_form = SampleFormClass(instance=sample)

    context = {
        "protocol": protocol,
        "protocol_form": protocol_form,
        "sample_form": sample_form,
        "analysis_type": protocol.analysis_type,
    }
    return render(request, "protocols/protocol_edit.html", context)


@login_required
@require_http_methods(["POST"])
@csrf_protect
def protocol_delete_view(request, pk):
    """
    Delete a protocol (only drafts can be deleted).
    """
    # Ensure user is a veterinarian
    try:
        veterinarian = request.user.veterinarian_profile
    except Veterinarian.DoesNotExist:
        messages.error(
            request, _("Debe completar su perfil de veterinario primero.")
        )
        return redirect("accounts:complete_profile")

    # Get protocol and ensure it belongs to this veterinarian
    protocol = get_object_or_404(Protocol, pk=pk)

    if protocol.veterinarian != veterinarian:
        return HttpResponseForbidden(
            _("No tiene permiso para eliminar este protocolo.")
        )

    if not protocol.is_deletable:
        messages.error(
            request,
            _("Solo los protocolos en borrador pueden ser eliminados."),
        )
        return redirect("protocols:protocol_detail", pk=protocol.pk)

    animal_id = protocol.animal_identification
    protocol.delete()
    messages.success(
        request,
        _("Protocolo para %(animal)s eliminado exitosamente.")
        % {"animal": animal_id},
    )
    return redirect("protocols:protocol_list")


@login_required
@require_http_methods(["POST"])
@csrf_protect
def protocol_submit_view(request, pk):
    """
    Submit a draft protocol.
    Generates temporary code and changes status to SUBMITTED.
    """
    # Ensure user is a veterinarian
    try:
        veterinarian = request.user.veterinarian_profile
    except Veterinarian.DoesNotExist:
        messages.error(
            request, _("Debe completar su perfil de veterinario primero.")
        )
        return redirect("accounts:complete_profile")

    # Get protocol and ensure it belongs to this veterinarian
    protocol = get_object_or_404(Protocol, pk=pk)

    if protocol.veterinarian != veterinarian:
        return HttpResponseForbidden(
            _("No tiene permiso para enviar este protocolo.")
        )

    try:
        protocol.submit()

        # Log status change
        ProtocolStatusHistory.log_status_change(
            protocol=protocol,
            new_status=Protocol.Status.SUBMITTED,
            changed_by=request.user,
            description="Protocol submitted by veterinarian",
        )

        # Send submission confirmation email
        _send_submission_confirmation_email(protocol)

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


@login_required
def protocol_select_type_view(request):
    """
    Show a page to select the type of protocol to create.
    """
    # Ensure user is a veterinarian
    try:
        request.user.veterinarian_profile
    except Veterinarian.DoesNotExist:
        messages.error(
            request, _("Debe completar su perfil de veterinario primero.")
        )
        return redirect("accounts:complete_profile")

    return render(request, "protocols/protocol_select_type.html")


# ============================================================================
# RECEPTION VIEWS
# ============================================================================


@login_required
@csrf_protect
def reception_search_view(request):
    """
    Search for a protocol by temporary code for reception.
    """
    # Check if user has staff/lab permissions
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("home")

    form = ReceptionSearchForm(request.POST or None)
    protocol = None

    # Handle GET request or invalid form
    if request.method != "POST" or not form.is_valid():
        context = {
            "form": form,
            "protocol": protocol,
        }
        return render(request, "protocols/reception_search.html", context)

    # POST with valid form - search for protocol
    temporary_code = form.cleaned_data["temporary_code"]

    try:
        protocol = Protocol.objects.select_related(
            "veterinarian__user",
            "cytology_sample",
            "histopathology_sample",
        ).get(temporary_code=temporary_code)
    except Protocol.DoesNotExist:
        messages.error(
            request,
            _("No se encontró ningún protocolo con el código %(code)s")
            % {"code": temporary_code},
        )
        context = {
            "form": form,
            "protocol": None,
        }
        return render(request, "protocols/reception_search.html", context)

    # Check protocol status and redirect or show info
    if protocol.status == Protocol.Status.DRAFT:
        messages.warning(
            request,
            _("Este protocolo aún está en borrador y no ha sido enviado."),
        )
    elif protocol.status == Protocol.Status.RECEIVED:
        messages.info(
            request,
            _("Este protocolo ya fue recibido el %(date)s. Número: %(number)s")
            % {
                "date": protocol.reception_date.strftime("%d/%m/%Y"),
                "number": protocol.protocol_number,
            },
        )
    else:
        # Protocol is ready for reception - redirect to confirmation
        return redirect("protocols:reception_confirm", pk=protocol.pk)

    context = {
        "form": form,
        "protocol": protocol,
    }
    return render(request, "protocols/reception_search.html", context)


@login_required
@csrf_protect
def reception_confirm_view(request, pk):
    """
    Confirm reception of a protocol and assign final protocol number.
    """
    # Check if user has staff/lab permissions
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("home")

    protocol = get_object_or_404(
        Protocol.objects.select_related(
            "veterinarian__user",
            "cytology_sample",
            "histopathology_sample",
        ),
        pk=pk,
    )

    # Check if protocol can be received
    if protocol.status not in [
        Protocol.Status.SUBMITTED,
        Protocol.Status.DRAFT,
    ]:
        messages.warning(request, _("Este protocolo ya fue procesado."))
        return redirect("protocols:reception_search")

    form = ReceptionForm(request.POST or None, protocol=protocol)

    # Handle GET request or invalid form
    if request.method != "POST" or not form.is_valid():
        context = {
            "protocol": protocol,
            "form": form,
        }
        return render(request, "protocols/reception_confirm.html", context)

    # Process reception (POST with valid form)
    sample_condition = form.cleaned_data["sample_condition"]
    reception_notes = form.cleaned_data.get("reception_notes", "")
    discrepancies = form.cleaned_data.get("discrepancies", "")

    # Update protocol
    protocol.receive(
        received_by=request.user,
        sample_condition=sample_condition,
        reception_notes=reception_notes,
        discrepancies=discrepancies,
    )

    # Update sample-specific fields for cytology
    if protocol.analysis_type == Protocol.AnalysisType.CYTOLOGY:
        slides_received = form.cleaned_data.get("number_slides_received")
        if slides_received is not None and hasattr(
            protocol, "cytology_sample"
        ):
            protocol.cytology_sample.number_slides_received = slides_received
            protocol.cytology_sample.save(
                update_fields=["number_slides_received"]
            )

    # Update sample-specific fields for histopathology
    if protocol.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY:
        jars_received = form.cleaned_data.get("number_jars_received")
        if jars_received is not None and hasattr(
            protocol, "histopathology_sample"
        ):
            protocol.histopathology_sample.number_jars_received = jars_received
            protocol.histopathology_sample.save(
                update_fields=["number_jars_received"]
            )

    # Log reception action
    ReceptionLog.log_action(
        protocol=protocol,
        action=ReceptionLog.Action.RECEIVED,
        user=request.user,
        notes=reception_notes,
    )

    # Log status change
    ProtocolStatusHistory.log_status_change(
        protocol=protocol,
        new_status=Protocol.Status.RECEIVED,
        changed_by=request.user,
        description=_("Muestra recibida en laboratorio"),
    )

    # Send email notification to veterinarian
    _send_reception_email(protocol)

    # Send discrepancy alert if issues found
    if discrepancies:
        _send_discrepancy_alert_email(
            protocol, discrepancies, sample_condition
        )

    messages.success(
        request,
        _("Muestra recibida exitosamente. Protocolo: %(number)s")
        % {"number": protocol.protocol_number},
    )

    return redirect("protocols:reception_detail", pk=protocol.pk)


@login_required
def reception_detail_view(request, pk):
    """
    Show reception confirmation and label printing options.
    """
    # Check if user has staff/lab permissions
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("home")

    protocol = get_object_or_404(
        Protocol.objects.select_related(
            "veterinarian__user",
            "received_by",
            "cytology_sample",
            "histopathology_sample",
        ),
        pk=pk,
    )

    context = {
        "protocol": protocol,
    }
    return render(request, "protocols/reception_detail.html", context)


@login_required
def reception_pending_view(request):
    """
    List protocols awaiting reception.
    """
    # Check if user has staff/lab permissions
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("home")

    # Get pending protocols (submitted but not received)
    protocols = (
        Protocol.objects.filter(status=Protocol.Status.SUBMITTED)
        .select_related(
            "veterinarian__user",
            "cytology_sample",
            "histopathology_sample",
        )
        .order_by("submission_date")
    )

    # Calculate days pending
    for protocol in protocols:
        days_pending = (date.today() - protocol.submission_date).days
        protocol.days_pending = days_pending

    context = {
        "protocols": protocols,
    }
    return render(request, "protocols/reception_pending.html", context)


@login_required
def reception_history_view(request):
    """
    Show reception history/log.
    """
    # Check if user has staff/lab permissions
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("home")

    # Get recent receptions
    logs = ReceptionLog.objects.select_related(
        "protocol",
        "protocol__veterinarian__user",
        "user",
    ).order_by("-created_at")[:100]

    context = {
        "logs": logs,
    }
    return render(request, "protocols/reception_history.html", context)


@login_required
def reception_label_pdf_view(request, pk):
    """
    Generate printable labels for a received sample.
    Returns a PDF with QR code and protocol information for 39x20mm tickets.
    """
    # Check if user has staff/lab permissions
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("home")

    protocol = get_object_or_404(
        Protocol.objects.select_related(
            "veterinarian__user",
            "cytology_sample",
            "histopathology_sample",
        ),
        pk=pk,
    )

    if not protocol.protocol_number:
        messages.error(
            request, _("Este protocolo aún no tiene número asignado.")
        )
        return redirect("protocols:reception_search")

    # 39x20 mm ticket paper configuration
    page_width = 39 * mm
    page_height = 20 * mm
    pagesize = (page_width, page_height)

    # QR code size for ticket
    qr_size = 12 * mm

    # Font sizes for ticket
    protocol_font_size = 8
    detail_font_size = 5

    # Margins for ticket
    margin = 1 * mm

    # Create PDF buffer
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=pagesize)

    # Generate QR code with full protocol URL
    qr_box_size = max(2, int(qr_size / 10))
    qr = qrcode.QRCode(version=1, box_size=qr_box_size, border=1)

    # Create full URL to protocol detail page using external_id
    protocol_url = request.build_absolute_uri(
        reverse(
            "protocols:protocol_public_detail",
            kwargs={"external_id": protocol.external_id},
        )
    )
    qr.add_data(protocol_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Save QR to buffer
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    qr_image = ImageReader(qr_buffer)

    # Layout for 39x20mm ticket
    # QR code on the left, text on the right
    qr_x = margin
    qr_y = margin
    text_x = qr_x + qr_size + 1 * mm

    # Protocol number (most important info)
    p.setFont("Helvetica-Bold", protocol_font_size)
    protocol_text = protocol.protocol_number
    # Truncate if too long for ticket
    if len(protocol_text) > 8:
        protocol_text = protocol_text[:8]
    p.drawString(text_x, qr_y + qr_size - 2 * mm, protocol_text)

    # Animal ID (second line)
    p.setFont("Helvetica", detail_font_size)
    animal_text = (
        protocol.animal_identification[:10]
        if len(protocol.animal_identification) > 10
        else protocol.animal_identification
    )
    p.drawString(text_x, qr_y + qr_size - 6 * mm, animal_text)

    # Species (third line)
    species_text = (
        protocol.species[:8] if len(protocol.species) > 8 else protocol.species
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
    p.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)

    p.showPage()
    p.save()

    buffer.seek(0)
    filename = f"label_{protocol.protocol_number.replace(' ', '_')}.pdf"
    return FileResponse(
        buffer,
        as_attachment=True,
        filename=filename,
    )


# ============================================================================
# PROCESSING VIEWS (STEP 05)
# ============================================================================


@login_required
def processing_dashboard_view(request):
    """
    Main processing dashboard showing samples in various processing stages.
    """
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("home")

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
    slides_mounted = Slide.objects.filter(estado=Slide.Status.MONTADO).count()
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

    context = {
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

    return render(request, "protocols/processing/dashboard.html", context)


@login_required
def processing_queue_view(request):
    """
    Show samples pending processing, filterable by type and stage.
    """
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("home")

    # Get filter parameters
    analysis_type = request.GET.get("type", "all")

    # Base queryset - received and processing protocols
    protocols = (
        Protocol.objects.filter(
            status__in=[Protocol.Status.RECEIVED, Protocol.Status.PROCESSING]
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
                1 for c in cassettes if c.estado == Cassette.Status.COMPLETADO
            )
            protocol.needs_cassettes = protocol.cassettes_count == 0

        slides = protocol.slides.all()
        protocol.slides_count = len(slides)
        protocol.slides_ready = sum(
            1 for s in slides if s.estado == Slide.Status.LISTO
        )
        protocol.needs_slides = protocol.slides_count == 0

    # Prepare filter fields for the UI component
    filter_fields = [
        {
            "name": "type",
            "label": "Tipo de Análisis",
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

    context = {
        "protocols": protocols,
        "analysis_type": analysis_type,
        "filter_fields": filter_fields,
    }

    return render(request, "protocols/processing/queue.html", context)


@login_required
def protocol_processing_status_view(request, pk):
    """
    Show complete processing status for a protocol with timeline.
    """
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("home")

    protocol = get_object_or_404(
        Protocol.objects.select_related(
            "veterinarian__user",
            "cytology_sample",
            "histopathology_sample",
        ),
        pk=pk,
    )

    # Get cassettes for histopathology
    cassettes = []
    if (
        protocol.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY
        and hasattr(protocol, "histopathology_sample")
    ):
        cassettes = (
            protocol.histopathology_sample.cassettes.all().prefetch_related(
                "cassette_slides__slide"
            )
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
    status_history = protocol.status_history.all().select_related("changed_by")

    context = {
        "protocol": protocol,
        "cassettes": cassettes,
        "slides": slides,
        "processing_logs": processing_logs,
        "status_history": status_history,
    }

    return render(
        request, "protocols/processing/protocol_status.html", context
    )


@login_required
@require_http_methods(["GET", "POST"])
def cassette_create_view(request, protocol_pk):
    """
    Create cassettes for a histopathology protocol.
    """
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("home")

    protocol = get_object_or_404(
        Protocol.objects.select_related("histopathology_sample"),
        pk=protocol_pk,
    )

    # Verify it's histopathology
    if protocol.analysis_type != Protocol.AnalysisType.HISTOPATHOLOGY:
        messages.error(
            request,
            _("Solo los protocolos de histopatología requieren cassettes."),
        )
        return redirect("protocols:processing_status", pk=protocol.pk)

    if not hasattr(protocol, "histopathology_sample"):
        messages.error(
            request, _("Este protocolo no tiene muestra de histopatología.")
        )
        return redirect("protocols:processing_status", pk=protocol.pk)

    # GET: Show form
    if request.method != "POST":
        # Get existing cassettes
        existing_cassettes = protocol.histopathology_sample.cassettes.all()

        context = {
            "protocol": protocol,
            "existing_cassettes": existing_cassettes,
        }
        return render(
            request, "protocols/processing/cassette_create.html", context
        )

    # POST: Create cassettes
    try:
        # Get form data
        cassette_count = int(request.POST.get("cassette_count", 1))
        if cassette_count < 1 or cassette_count > 20:
            raise ValueError("Invalid cassette count")

        # Create cassettes
        created_cassettes = []
        for i in range(cassette_count):
            material = request.POST.get(f"material_{i}", "")
            tipo = request.POST.get(f"tipo_{i}", Cassette.CassetteType.NORMAL)
            color = request.POST.get(
                f"color_{i}", Cassette.CassetteColor.BLANCO
            )
            observaciones = request.POST.get(f"observaciones_{i}", "")

            if not material:
                continue

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
            _(f"Se crearon {len(created_cassettes)} cassettes exitosamente."),
        )
        return redirect("protocols:slide_register", protocol_pk=protocol.pk)

    except Exception as e:
        logger.error(
            f"Error creating cassettes for protocol {protocol.pk}: {e}"
        )
        messages.error(
            request,
            _("Error al crear cassettes. Por favor intente nuevamente."),
        )
        return redirect("protocols:cassette_create", protocol_pk=protocol.pk)


@login_required
@require_http_methods(["GET", "POST"])
def slide_register_view(request, protocol_pk):
    """
    Register slides for a protocol with interactive cassette-slide relationship.
    This implements the visual UI shown by the user.
    """
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("home")

    protocol = get_object_or_404(
        Protocol.objects.select_related(
            "veterinarian__user",
            "cytology_sample",
            "histopathology_sample",
        ),
        pk=protocol_pk,
    )

    # GET: Show interactive slide registration interface
    if request.method != "POST":
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

    # POST: Save slide registrations
    try:
        import json

        # Get form data
        comments = request.POST.get("comments", "")
        staining_technique = request.POST.get(
            "staining_technique", "Hematoxilina-Eosina"
        )

        # Get slide data from JSON (sent from Vue.js frontend)
        slides_data = json.loads(request.POST.get("slides_data", "[]"))
        relationships_data = json.loads(
            request.POST.get("relationships_data", "{}")
        )

        # Create slides and relationships
        created_slides = []

        for slide_number in slides_data:
            # Check if slide already exists
            existing_slide = Slide.objects.filter(
                protocol=protocol, campo=slide_number
            ).first()

            if existing_slide:
                slide = existing_slide
            else:
                # Create new slide
                slide = Slide.objects.create(
                    protocol=protocol,
                    campo=slide_number,
                    tecnica_coloracion=staining_technique,
                    observaciones=comments,
                    cytology_sample=protocol.cytology_sample
                    if protocol.analysis_type == Protocol.AnalysisType.CYTOLOGY
                    else None,
                )

                # Log slide creation
                ProcessingLog.log_action(
                    protocol=protocol,
                    etapa=ProcessingLog.Stage.MONTAJE,
                    usuario=request.user,
                    slide=slide,
                    observaciones=f"Slide {slide.codigo_portaobjetos} creado",
                )

                created_slides.append(slide)

        # Create cassette-slide relationships
        created_relationships = 0
        for relationship_key, cassette_id in relationships_data.items():
            # Parse key: "slideNumber-position"
            slide_number, position = map(int, relationship_key.split("-"))

            # Get slide
            slide = Slide.objects.filter(
                protocol=protocol, campo=slide_number
            ).first()
            if not slide:
                continue

            # Get cassette
            try:
                cassette = Cassette.objects.get(pk=cassette_id)
            except Cassette.DoesNotExist:
                continue

            # Map position number to position choice
            position_mapping = {
                1: CassetteSlide.Position.SUPERIOR,
                2: CassetteSlide.Position.INFERIOR,
            }
            position_choice = position_mapping.get(
                position, CassetteSlide.Position.COMPLETO
            )

            # Check if relationship already exists
            existing_rel = CassetteSlide.objects.filter(
                cassette=cassette, slide=slide
            ).first()

            if not existing_rel:
                # Create relationship
                CassetteSlide.objects.create(
                    cassette=cassette,
                    slide=slide,
                    posicion=position_choice,
                    coloracion=staining_technique,
                )
                created_relationships += 1

        # Update slide stages
        for slide in created_slides:
            slide.update_stage("montaje")

        # Update protocol status if needed
        if protocol.status == Protocol.Status.RECEIVED:
            protocol.status = Protocol.Status.PROCESSING
            protocol.save(update_fields=["status"])

            ProtocolStatusHistory.log_status_change(
                protocol=protocol,
                new_status=Protocol.Status.PROCESSING,
                changed_by=request.user,
                description=f"Iniciado procesamiento - {len(created_slides)} slides creados",
            )

        messages.success(
            request,
            _(
                f"Se registraron {len(created_slides)} slides y {created_relationships} "
                f"relaciones cassette-slide exitosamente."
            ),
        )
        return redirect("protocols:processing_status", pk=protocol.pk)

    except Exception as e:
        logger.error(
            f"Error registering slides for protocol {protocol.pk}: {e}"
        )
        messages.error(
            request,
            _("Error al registrar slides. Por favor intente nuevamente."),
        )
        return redirect("protocols:slide_register", protocol_pk=protocol.pk)


@login_required
@require_http_methods(["POST"])
def slide_update_stage_view(request, slide_pk):
    """
    Update slide processing stage (montaje, coloración, listo).
    """
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("home")

    slide = get_object_or_404(Slide, pk=slide_pk)

    stage = request.POST.get("stage")
    observaciones = request.POST.get("observaciones", "")

    if stage in ["montaje", "coloracion"]:
        slide.update_stage(stage)

        # Log action
        etapa_mapping = {
            "montaje": ProcessingLog.Stage.MONTAJE,
            "coloracion": ProcessingLog.Stage.COLORACION,
        }

        ProcessingLog.log_action(
            protocol=slide.protocol,
            etapa=etapa_mapping[stage],
            usuario=request.user,
            slide=slide,
            observaciones=observaciones,
        )

        messages.success(
            request,
            _(f"Slide {slide.codigo_portaobjetos} actualizado a {stage}."),
        )
    elif stage == "listo":
        slide.mark_ready()
        messages.success(
            request,
            _(f"Slide {slide.codigo_portaobjetos} marcado como listo."),
        )
    else:
        messages.error(request, _("Etapa no válida."))

    return redirect("protocols:processing_status", pk=slide.protocol.pk)


@login_required
@require_http_methods(["POST"])
def slide_update_quality_view(request, slide_pk):
    """
    Update slide quality assessment.
    """
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("home")

    slide = get_object_or_404(Slide, pk=slide_pk)

    quality = request.POST.get("quality")
    observaciones = request.POST.get("observaciones", "")

    if quality in [choice[0] for choice in Slide.Quality.choices]:
        slide.calidad = quality
        if observaciones:
            slide.observaciones = observaciones
        slide.save(update_fields=["calidad", "observaciones"])

        messages.success(
            request,
            _(f"Calidad de slide {slide.codigo_portaobjetos} actualizada."),
        )
    else:
        messages.error(request, _("Calidad no válida."))

    return redirect("protocols:processing_status", pk=slide.protocol.pk)
