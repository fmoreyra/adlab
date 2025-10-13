"""
Views for work order generation and management.
"""

import io
import logging
import os
import tempfile
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from protocols.emails import send_work_order_notification
from protocols.forms_workorder import (
    ProtocolSelectionForm,
    WorkOrderCreateForm,
    WorkOrderFilterForm,
)
from protocols.models import (
    PricingCatalog,
    Protocol,
    WorkOrder,
    WorkOrderService,
)

logger = logging.getLogger(__name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _send_work_order_notification(work_order):
    """
    Send work order notification email to veterinarian.

    Args:
        work_order: WorkOrder instance that was created

    Returns:
        bool: True if email was queued successfully, False otherwise
    """
    try:
        email_log = send_work_order_notification(
            work_order=work_order,
            work_order_pdf_path=None,  # PDF generation can be added later
        )
        if email_log:
            logger.info(
                f"Work order email queued for {work_order.order_number} "
                f"(EmailLog ID: {email_log.id})"
            )
            return True
        else:
            logger.info(
                f"Work order email skipped for {work_order.order_number} "
                "(veterinarian preferences)"
            )
            return False
    except Exception as e:
        logger.error(
            f"Failed to queue work order email for {work_order.pk}: {e}"
        )
        return False


# =============================================================================
# WORK ORDER LIST AND SEARCH
# =============================================================================


@login_required
@csrf_protect
def workorder_list_view(request):
    """List all work orders with filtering."""
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("protocols:protocol_list")

    # Base queryset
    work_orders = (
        WorkOrder.objects.select_related(
            "veterinarian__user",
            "created_by",
        )
        .prefetch_related(
            "services__protocol",
        )
        .order_by("-created_at")
    )

    # Apply filters
    filter_form = WorkOrderFilterForm(request.GET)
    if filter_form.is_valid():
        order_number = filter_form.cleaned_data.get("order_number")
        veterinarian = filter_form.cleaned_data.get("veterinarian")
        status = filter_form.cleaned_data.get("status")
        payment_status = filter_form.cleaned_data.get("payment_status")
        date_from = filter_form.cleaned_data.get("date_from")
        date_to = filter_form.cleaned_data.get("date_to")

        if order_number:
            work_orders = work_orders.filter(
                order_number__icontains=order_number
            )

        if veterinarian:
            work_orders = work_orders.filter(veterinarian=veterinarian)

        if status:
            work_orders = work_orders.filter(status=status)

        if payment_status:
            work_orders = work_orders.filter(payment_status=payment_status)

        if date_from:
            work_orders = work_orders.filter(issue_date__gte=date_from)

        if date_to:
            work_orders = work_orders.filter(issue_date__lte=date_to)

    context = {
        "work_orders": work_orders,
        "filter_form": filter_form,
        "title": _("Órdenes de Trabajo"),
    }
    return render(request, "protocols/workorder/list.html", context)


@login_required
@csrf_protect
def workorder_pending_protocols_view(request):
    """List protocols ready for work order generation."""
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("protocols:protocol_list")

    # Protocols that are READY or REPORT_SENT and don't have work orders
    protocols = (
        Protocol.objects.filter(
            status__in=[Protocol.Status.READY, Protocol.Status.REPORT_SENT],
            work_order__isnull=True,
        )
        .select_related(
            "veterinarian__user",
        )
        .order_by("veterinarian", "-submission_date")
    )

    # Group by veterinarian for easier processing
    protocols_by_vet = {}
    for protocol in protocols:
        vet_key = protocol.veterinarian.id
        if vet_key not in protocols_by_vet:
            protocols_by_vet[vet_key] = {
                "veterinarian": protocol.veterinarian,
                "protocols": [],
            }
        protocols_by_vet[vet_key]["protocols"].append(protocol)

    context = {
        "protocols_by_vet": protocols_by_vet.values(),
        "title": _("Protocolos sin Orden de Trabajo"),
    }
    return render(
        request, "protocols/workorder/pending_protocols.html", context
    )


# =============================================================================
# WORK ORDER CREATION
# =============================================================================


@login_required
@csrf_protect
def workorder_select_protocols_view(request, veterinarian_id):
    """Select protocols to include in a work order."""
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("protocols:protocol_list")

    from accounts.models import Veterinarian

    veterinarian = get_object_or_404(Veterinarian, pk=veterinarian_id)

    # Early return: GET request
    if request.method != "POST":
        form = ProtocolSelectionForm(veterinarian=veterinarian)
        context = {
            "form": form,
            "veterinarian": veterinarian,
            "title": _("Seleccionar Protocolos - {}").format(
                veterinarian.user.get_full_name()
            ),
        }
        return render(
            request, "protocols/workorder/select_protocols.html", context
        )

    # POST: Process selection
    form = ProtocolSelectionForm(request.POST, veterinarian=veterinarian)

    # Early return: invalid form
    if not form.is_valid():
        context = {
            "form": form,
            "veterinarian": veterinarian,
            "title": _("Seleccionar Protocolos - {}").format(
                veterinarian.user.get_full_name()
            ),
        }
        return render(
            request, "protocols/workorder/select_protocols.html", context
        )

    # Success: redirect to work order creation with selected protocols
    protocols = form.cleaned_data["protocols"]
    protocol_ids = ",".join(str(p.id) for p in protocols)

    return redirect(
        "protocols:workorder_create_with_protocols", protocol_ids=protocol_ids
    )


@login_required
@csrf_protect
def workorder_create_view(request, protocol_ids):
    """Create a new work order for selected protocols."""
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("protocols:protocol_list")

    # Parse protocol IDs
    protocol_id_list = [int(pid) for pid in protocol_ids.split(",")]
    protocols = (
        Protocol.objects.filter(id__in=protocol_id_list)
        .select_related(
            "veterinarian__user",
        )
        .order_by("-submission_date")
    )

    # Validate protocols
    if not protocols.exists():
        messages.error(request, _("No se encontraron protocolos válidos."))
        return redirect("protocols:workorder_pending_protocols")

    # Validate all from same veterinarian
    veterinarians = set(p.veterinarian for p in protocols)
    if len(veterinarians) > 1:
        messages.error(
            request, _("Todos los protocolos deben ser del mismo veterinario.")
        )
        return redirect("protocols:workorder_pending_protocols")

    veterinarian = list(veterinarians)[0]

    # Calculate services and pricing
    services_data = _calculate_services(protocols)

    # Early return: GET request
    if request.method != "POST":
        form = WorkOrderCreateForm(protocols=protocols)
        context = {
            "form": form,
            "protocols": protocols,
            "veterinarian": veterinarian,
            "services_data": services_data,
            "title": _("Crear Orden de Trabajo"),
        }
        return render(request, "protocols/workorder/create.html", context)

    # POST: Create work order
    form = WorkOrderCreateForm(request.POST, protocols=protocols)

    # Early return: invalid form
    if not form.is_valid():
        context = {
            "form": form,
            "protocols": protocols,
            "veterinarian": veterinarian,
            "services_data": services_data,
            "title": _("Crear Orden de Trabajo"),
        }
        return render(request, "protocols/workorder/create.html", context)

    # Create work order with services
    try:
        work_order = _create_work_order_with_services(
            form=form,
            protocols=protocols,
            services_data=services_data,
            created_by=request.user,
        )

        # Send work order notification email
        _send_work_order_notification(work_order)

        messages.success(
            request,
            _(
                "Orden de trabajo {} creada y enviada por email exitosamente."
            ).format(work_order.order_number),
        )
        return redirect("protocols:workorder_detail", pk=work_order.pk)

    except Exception as e:
        logger.error(f"Error creating work order: {e}")
        messages.error(
            request,
            _(
                "Error al crear la orden de trabajo. Por favor intente nuevamente."
            ),
        )
        context = {
            "form": form,
            "protocols": protocols,
            "veterinarian": veterinarian,
            "services_data": services_data,
            "title": _("Crear Orden de Trabajo"),
        }
        return render(request, "protocols/workorder/create.html", context)


def _calculate_services(protocols):
    """
    Calculate service line items for protocols.

    Args:
        protocols: QuerySet of Protocol objects

    Returns:
        dict: Service data with items, subtotal, and total
    """
    services = []
    subtotal = Decimal("0")

    for protocol in protocols:
        # Determine service type based on analysis type and sample details
        if protocol.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY:
            service_type = "histopatologia_2a5_piezas"
            description = (
                f"Análisis histopatológico - {protocol.animal_identification}"
            )
        else:  # Cytology
            service_type = "citologia"
            description = (
                f"Análisis citopatológico - {protocol.animal_identification}"
            )

        # Get current price from catalog
        pricing = PricingCatalog.get_current_price(service_type)

        if pricing:
            unit_price = pricing.price
        else:
            # Default prices if not in catalog
            unit_price = (
                Decimal("14.04")
                if protocol.analysis_type
                == Protocol.AnalysisType.HISTOPATHOLOGY
                else Decimal("5.40")
            )

        item_subtotal = unit_price * 1  # quantity = 1 per protocol

        services.append(
            {
                "protocol": protocol,
                "description": description,
                "service_type": service_type,
                "quantity": 1,
                "unit_price": unit_price,
                "subtotal": item_subtotal,
                "discount": Decimal("0"),
            }
        )

        subtotal += item_subtotal

    return {
        "services": services,
        "subtotal": subtotal,
        "total": subtotal,
    }


@transaction.atomic
def _create_work_order_with_services(
    form, protocols, services_data, created_by
):
    """
    Create work order and its service line items.

    Args:
        form: Validated WorkOrderCreateForm
        protocols: QuerySet of protocols
        services_data: Service calculation data
        created_by: User creating the work order

    Returns:
        WorkOrder: Created work order instance
    """
    # Create work order
    work_order = form.save(commit=False)
    work_order.total_amount = services_data["total"]
    work_order.created_by = created_by
    work_order.save()

    # Create service line items
    for service_data in services_data["services"]:
        WorkOrderService.objects.create(
            work_order=work_order,
            protocol=service_data["protocol"],
            description=service_data["description"],
            service_type=service_data["service_type"],
            quantity=service_data["quantity"],
            unit_price=service_data["unit_price"],
            discount=service_data["discount"],
        )

        # Link protocol to work order
        protocol = service_data["protocol"]
        protocol.work_order = work_order
        protocol.save(update_fields=["work_order"])

    return work_order


# =============================================================================
# WORK ORDER DETAIL AND ACTIONS
# =============================================================================


@login_required
@csrf_protect
def workorder_detail_view(request, pk):
    """View work order details."""
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("protocols:protocol_list")

    work_order = get_object_or_404(
        WorkOrder.objects.select_related(
            "veterinarian__user",
            "created_by",
        ).prefetch_related(
            "services__protocol",
        ),
        pk=pk,
    )

    context = {
        "work_order": work_order,
        "title": _("Orden de Trabajo - {}").format(work_order.order_number),
    }
    return render(request, "protocols/workorder/detail.html", context)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def workorder_issue_view(request, pk):
    """Issue (finalize) a draft work order."""
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("protocols:protocol_list")

    work_order = get_object_or_404(WorkOrder, pk=pk)

    # Early return: check if can be issued
    if work_order.status != WorkOrder.Status.DRAFT:
        messages.error(
            request, _("Solo las órdenes en borrador pueden ser emitidas.")
        )
        return redirect("protocols:workorder_detail", pk=work_order.pk)

    try:
        work_order.issue()
        messages.success(
            request,
            _("Orden de trabajo {} emitida correctamente.").format(
                work_order.order_number
            ),
        )
    except Exception as e:
        logger.error(f"Error issuing work order {work_order.pk}: {e}")
        messages.error(request, _("Error al emitir la orden de trabajo."))

    return redirect("protocols:workorder_detail", pk=work_order.pk)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def workorder_send_view(request, pk):
    """Send work order to finance office."""
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("protocols:protocol_list")

    work_order = get_object_or_404(WorkOrder, pk=pk)

    # Early return: check if can be sent
    if work_order.status not in [
        WorkOrder.Status.DRAFT,
        WorkOrder.Status.ISSUED,
    ]:
        messages.error(
            request,
            _("Solo las órdenes en borrador o emitidas pueden ser enviadas."),
        )
        return redirect("protocols:workorder_detail", pk=work_order.pk)

    try:
        # Generate PDF if not exists
        if not work_order.pdf_path or not os.path.exists(
            os.path.join(settings.MEDIA_ROOT, work_order.pdf_path)
        ):
            _generate_workorder_pdf(work_order)

        # Mark as sent
        work_order.mark_as_sent()

        messages.success(
            request,
            _("Orden de trabajo {} marcada como enviada.").format(
                work_order.order_number
            ),
        )
    except Exception as e:
        logger.error(f"Error sending work order {work_order.pk}: {e}")
        messages.error(request, _("Error al enviar la orden de trabajo."))

    return redirect("protocols:workorder_detail", pk=work_order.pk)


# =============================================================================
# PDF GENERATION
# =============================================================================


@login_required
def workorder_pdf_view(request, pk):
    """Generate and serve work order PDF."""
    if not request.user.is_staff:
        messages.error(
            request, _("No tiene permisos para acceder a esta función.")
        )
        return redirect("protocols:protocol_list")

    work_order = get_object_or_404(
        WorkOrder.objects.select_related(
            "veterinarian__user",
        ).prefetch_related(
            "services__protocol",
        ),
        pk=pk,
    )

    try:
        pdf_buffer = _generate_workorder_pdf_buffer(work_order)
        filename = work_order.generate_pdf_filename()

        response = HttpResponse(
            pdf_buffer.getvalue(), content_type="application/pdf"
        )
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response

    except Exception as e:
        logger.error(f"Error generating work order PDF: {e}")
        messages.error(
            request, _("Error al generar el PDF de la orden de trabajo.")
        )
        return redirect("protocols:workorder_detail", pk=work_order.pk)


def _generate_workorder_pdf_buffer(work_order):
    """
    Generate work order PDF and return as buffer.

    Args:
        work_order: WorkOrder instance

    Returns:
        io.BytesIO: PDF buffer
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=12,
        alignment=1,  # Center
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#333333"),
        spaceAfter=10,
    )

    normal_style = styles["Normal"]

    # Header
    story.append(Paragraph("ORDEN DE TRABAJO", title_style))
    story.append(Paragraph(f"N° {work_order.order_number}", heading_style))
    story.append(Spacer(1, 0.2 * inch))

    # Date and client info
    story.append(
        Paragraph(
            f"<b>Fecha:</b> {work_order.issue_date.strftime('%d/%m/%Y')}",
            normal_style,
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("<b>Cliente:</b>", heading_style))
    story.append(Paragraph(work_order.get_billing_name(), normal_style))

    if work_order.cuit_cuil:
        story.append(
            Paragraph(
                f"<b>CUIT/CUIL:</b> {work_order.cuit_cuil}", normal_style
            )
        )

    if work_order.iva_condition:
        story.append(
            Paragraph(
                f"<b>Condición IVA:</b> {work_order.get_iva_condition_display()}",
                normal_style,
            )
        )

    story.append(Spacer(1, 0.3 * inch))

    # Services table
    story.append(Paragraph("<b>SERVICIOS:</b>", heading_style))
    story.append(Spacer(1, 0.1 * inch))

    table_data = [
        ["Protocolo", "Descripción", "Cantidad", "P. Unit.", "Subtotal"]
    ]

    for service in work_order.services.all():
        row = [
            service.protocol.protocol_number or "-",
            service.description[:60],
            str(service.quantity),
            f"${service.unit_price:.2f}",
            f"${service.subtotal:.2f}",
        ]
        table_data.append(row)

    table = Table(
        table_data,
        colWidths=[1.2 * inch, 3 * inch, 0.8 * inch, 1 * inch, 1 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    story.append(table)
    story.append(Spacer(1, 0.3 * inch))

    # Totals
    totals_data = [
        ["SUBTOTAL:", f"${work_order.total_amount:.2f}"],
        ["PAGO ADELANTADO:", f"${work_order.advance_payment:.2f}"],
        ["SALDO PENDIENTE:", f"${work_order.balance_due:.2f}"],
    ]

    totals_table = Table(totals_data, colWidths=[4.5 * inch, 1.5 * inch])
    totals_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("LINEABOVE", (0, 0), (-1, 0), 1, colors.black),
                ("LINEABOVE", (0, -1), (-1, -1), 2, colors.black),
            ]
        )
    )

    story.append(totals_table)

    # Observations
    if work_order.observations:
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("<b>Observaciones:</b>", heading_style))
        story.append(Paragraph(work_order.observations, normal_style))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def _generate_workorder_pdf(work_order):
    """
    Generate work order PDF and save to file using atomic operations.

    Args:
        work_order: WorkOrder instance
    """
    # Generate PDF buffer
    pdf_buffer = _generate_workorder_pdf_buffer(work_order)

    # Save to file using atomic operations
    workorders_dir = os.path.join(settings.MEDIA_ROOT, "workorders")
    os.makedirs(workorders_dir, exist_ok=True)

    filename = work_order.generate_pdf_filename()
    filepath = os.path.join(workorders_dir, filename)
    tmp_path = None

    try:
        # Write to temporary file first
        with tempfile.NamedTemporaryFile(
            mode="wb", delete=False, dir=workorders_dir, suffix=".tmp"
        ) as tmp_file:
            tmp_file.write(pdf_buffer.getvalue())
            tmp_path = tmp_file.name

        # Atomic rename to final location
        os.replace(tmp_path, filepath)
        tmp_path = None  # Success, no cleanup needed

    except Exception:
        # Cleanup temporary file on error
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    # Update work order with PDF path
    work_order.pdf_path = os.path.join("workorders", filename)
    work_order.save(update_fields=["pdf_path"])

    logger.info(f"Work order PDF generated: {filepath}")
