"""
Views for report generation and management.
"""
import hashlib
import io
import logging
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from protocols.emails import send_report_ready_notification
from protocols.forms_reports import (
    CassetteObservationFormSet,
    ReportCreateForm,
    ReportSendForm,
)
from protocols.models import Protocol, Report

logger = logging.getLogger(__name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _send_report_ready_notification(report, pdf_path):
    """
    Send report ready notification email with PDF attachment.
    
    Args:
        report: Report instance that was finalized
        pdf_path: Path to the generated PDF file
    
    Returns:
        bool: True if email was queued successfully, False otherwise
    """
    try:
        email_log = send_report_ready_notification(
            protocol=report.protocol,
            report_pdf_path=pdf_path
        )
        if email_log:
            logger.info(
                f"Report ready email queued for report {report.pk} "
                f"(EmailLog ID: {email_log.id})"
            )
            return True
        else:
            logger.info(
                f"Report ready email skipped for report {report.pk} "
                "(veterinarian preferences)"
            )
            return False
    except Exception as e:
        logger.error(
            f"Failed to queue report ready email for report {report.pk}: {e}"
        )
        return False


# =============================================================================
# REPORT LIST AND SEARCH
# =============================================================================


@login_required
@csrf_protect
def report_pending_list_view(request):
    """List protocols that are ready for report generation."""
    if not request.user.is_staff:
        messages.error(
            request,
            _("No tiene permisos para acceder a esta función.")
        )
        return redirect("protocols:protocol_list")

    # Protocols that are READY status and don't have reports yet
    protocols = Protocol.objects.filter(
        status=Protocol.Status.READY
    ).select_related(
        "veterinarian__user",
        "cytology_sample",
        "histopathology_sample",
    ).prefetch_related(
        "histopathology_sample__cassettes",
        "slides",
    ).order_by("-reception_date")

    # Filter out protocols that already have reports
    protocols_without_reports = []
    for protocol in protocols:
        if not protocol.reports.exists():
            protocols_without_reports.append(protocol)

    context = {
        "protocols": protocols_without_reports,
        "title": _("Protocolos Pendientes de Informe"),
    }
    return render(request, "protocols/reports/pending_list.html", context)


@login_required
@csrf_protect
def report_history_view(request):
    """View history of generated reports."""
    if not request.user.is_staff:
        messages.error(
            request,
            _("No tiene permisos para acceder a esta función.")
        )
        return redirect("protocols:protocol_list")

    reports = Report.objects.select_related(
        "protocol",
        "histopathologist",
        "veterinarian",
    ).order_by("-created_at")

    context = {
        "reports": reports,
        "title": _("Historial de Informes"),
    }
    return render(request, "protocols/reports/history.html", context)


# =============================================================================
# REPORT CREATION AND EDITING
# =============================================================================


@login_required
@csrf_protect
def report_create_view(request, protocol_id):
    """Create a new report for a protocol."""
    if not request.user.is_staff:
        messages.error(
            request,
            _("No tiene permisos para acceder a esta función.")
        )
        return redirect("protocols:protocol_list")

    protocol = get_object_or_404(
        Protocol.objects.select_related(
            "veterinarian__user",
            "histopathology_sample",
        ).prefetch_related(
            "histopathology_sample__cassettes",
        ),
        pk=protocol_id
    )

    # Check if protocol is ready for report
    if protocol.status not in [Protocol.Status.READY, Protocol.Status.PROCESSING]:
        messages.error(
            request,
            _("El protocolo debe estar en estado 'Listo' para generar el informe.")
        )
        return redirect("protocols:protocol_detail", pk=protocol.pk)

    # Check if report already exists
    if protocol.reports.exists():
        existing_report = protocol.reports.first()
        messages.warning(
            request,
            _("Ya existe un informe para este protocolo.")
        )
        return redirect("protocols:report_detail", pk=existing_report.pk)

    form = ReportCreateForm(
        request.POST or None,
        protocol=protocol,
    )

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            report = form.save(commit=False)
            report.protocol = protocol
            report.veterinarian = protocol.veterinarian
            report.save()

            messages.success(
                request,
                _("Informe creado exitosamente. Ahora puede agregar observaciones por cassette.")
            )
            return redirect("protocols:report_edit", pk=report.pk)

    context = {
        "form": form,
        "protocol": protocol,
        "title": _("Crear Informe - %(protocol)s") % {"protocol": protocol.protocol_number},
    }
    return render(request, "protocols/reports/create.html", context)


@login_required
@csrf_protect
def report_edit_view(request, pk):
    """Edit an existing report (draft only)."""
    if not request.user.is_staff:
        messages.error(
            request,
            _("No tiene permisos para acceder a esta función.")
        )
        return redirect("protocols:protocol_list")

    report = get_object_or_404(
        Report.objects.select_related(
            "protocol",
            "histopathologist",
            "veterinarian",
        ).prefetch_related(
            "cassette_observations__cassette",
        ),
        pk=pk
    )

    if not report.can_edit():
        messages.error(
            request,
            _("Solo se pueden editar informes en estado borrador.")
        )
        return redirect("protocols:report_detail", pk=report.pk)

    form = ReportCreateForm(
        request.POST or None,
        instance=report,
        protocol=report.protocol,
    )
    
    formset = CassetteObservationFormSet(
        request.POST or None,
        instance=report,
    )

    if request.method == "POST" and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            report = form.save()
            formset.save()

            messages.success(
                request,
                _("Informe actualizado exitosamente.")
            )
            return redirect("protocols:report_detail", pk=report.pk)

    context = {
        "form": form,
        "formset": formset,
        "report": report,
        "protocol": report.protocol,
        "title": _("Editar Informe - %(protocol)s") % {"protocol": report.protocol.protocol_number},
    }
    return render(request, "protocols/reports/edit.html", context)


@login_required
def report_detail_view(request, pk):
    """View report details."""
    report = get_object_or_404(
        Report.objects.select_related(
            "protocol",
            "histopathologist",
            "veterinarian",
        ).prefetch_related(
            "cassette_observations__cassette",
            "images",
        ),
        pk=pk
    )

    # Check permissions
    is_owner = False
    if hasattr(request.user, "veterinarian_profile"):
        is_owner = request.user.veterinarian_profile == report.veterinarian
    
    if not (request.user.is_staff or is_owner):
        messages.error(
            request,
            _("No tiene permisos para ver este informe.")
        )
        return redirect("protocols:protocol_list")

    context = {
        "report": report,
        "protocol": report.protocol,
        "title": _("Informe - %(protocol)s") % {"protocol": report.protocol.protocol_number},
    }
    return render(request, "protocols/reports/detail.html", context)


# =============================================================================
# REPORT FINALIZATION AND PDF GENERATION
# =============================================================================


def generate_report_pdf(report):
    """
    Generate PDF for a report using ReportLab.
    Returns tuple of (pdf_buffer, pdf_hash).
    """
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )
    
    # Container for PDF elements
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=1,  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=12,
    )
    
    normal_style = styles['Normal']
    
    # Title
    elements.append(Paragraph("INFORME HISTOPATOLÓGICO", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Protocol information
    protocol = report.protocol
    protocol_data = [
        ["Protocolo:", protocol.protocol_number or "-"],
        ["Fecha de Informe:", report.report_date.strftime("%d/%m/%Y")],
        ["Versión:", str(report.version)],
    ]
    
    protocol_table = Table(protocol_data, colWidths=[2*inch, 4*inch])
    protocol_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONT', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(protocol_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Patient information
    elements.append(Paragraph("DATOS DEL PACIENTE", heading_style))
    patient_data = [
        ["Especie:", protocol.species],
        ["Raza:", protocol.breed or "-"],
        ["Edad:", protocol.age or "-"],
        ["Sexo:", protocol.get_sex_display()],
        ["Identificación:", protocol.animal_identification or "-"],
    ]
    
    patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
    patient_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONT', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(patient_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Veterinarian information
    elements.append(Paragraph("VETERINARIO SOLICITANTE", heading_style))
    vet = report.veterinarian
    vet_data = [
        ["Nombre:", vet.get_full_name()],
        ["Matrícula:", vet.license_number],
        ["Email:", vet.email],
        ["Teléfono:", vet.phone or "-"],
    ]
    
    vet_table = Table(vet_data, colWidths=[2*inch, 4*inch])
    vet_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONT', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(vet_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Macroscopic observations
    if report.macroscopic_observations:
        elements.append(Paragraph("DESCRIPCIÓN MACROSCÓPICA", heading_style))
        elements.append(Paragraph(report.macroscopic_observations, normal_style))
        elements.append(Spacer(1, 0.2*inch))
    
    # Microscopic observations
    if report.microscopic_observations:
        elements.append(Paragraph("DESCRIPCIÓN MICROSCÓPICA", heading_style))
        elements.append(Paragraph(report.microscopic_observations, normal_style))
        elements.append(Spacer(1, 0.2*inch))
    
    # Cassette observations
    cassette_observations = report.cassette_observations.order_by('order', 'cassette__codigo_cassette')
    if cassette_observations.exists():
        elements.append(Paragraph("OBSERVACIONES POR CASSETTE", heading_style))
        for obs in cassette_observations:
            cassette_title = f"Cassette {obs.cassette.codigo_cassette}"
            elements.append(Paragraph(cassette_title, ParagraphStyle(
                'CassetteTitle',
                parent=styles['Heading3'],
                fontSize=10,
                textColor=colors.HexColor('#555555'),
                spaceAfter=6,
                spaceBefore=6,
            )))
            elements.append(Paragraph(obs.observations, normal_style))
            if obs.partial_diagnosis:
                elements.append(Paragraph(f"<b>Diagnóstico:</b> {obs.partial_diagnosis}", normal_style))
            elements.append(Spacer(1, 0.15*inch))
    
    # Diagnosis
    elements.append(Paragraph("DIAGNÓSTICO", heading_style))
    elements.append(Paragraph(report.diagnosis, ParagraphStyle(
        'Diagnosis',
        parent=normal_style,
        fontSize=11,
        textColor=colors.HexColor('#000000'),
        spaceAfter=12,
        fontName='Helvetica-Bold',
    )))
    
    # Comments
    if report.comments:
        elements.append(Paragraph("COMENTARIOS", heading_style))
        elements.append(Paragraph(report.comments, normal_style))
        elements.append(Spacer(1, 0.2*inch))
    
    # Recommendations
    if report.recommendations:
        elements.append(Paragraph("RECOMENDACIONES", heading_style))
        elements.append(Paragraph(report.recommendations, normal_style))
        elements.append(Spacer(1, 0.2*inch))
    
    # Signature
    elements.append(Spacer(1, 0.5*inch))
    histopath = report.histopathologist
    
    # Add signature image if available
    if histopath.signature_image and os.path.exists(histopath.signature_image.path):
        try:
            sig_img = Image(histopath.signature_image.path, width=2*inch, height=1*inch)
            elements.append(sig_img)
        except Exception as e:
            logger.warning(f"Could not load signature image: {e}")
    
    signature_data = [
        [histopath.get_formal_name()],
        [f"Mat. {histopath.license_number}"],
    ]
    if histopath.position:
        signature_data.append([histopath.position])
    
    signature_table = Table(signature_data, colWidths=[4*inch])
    signature_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(signature_table)
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF content and calculate hash
    pdf_content = buffer.getvalue()
    pdf_hash = hashlib.sha256(pdf_content).hexdigest()
    
    buffer.seek(0)
    return buffer, pdf_hash


@login_required
@csrf_protect
@require_http_methods(["POST"])
def report_finalize_view(request, pk):
    """Finalize report and generate PDF."""
    if not request.user.is_staff:
        messages.error(
            request,
            _("No tiene permisos para acceder a esta función.")
        )
        return redirect("protocols:protocol_list")

    report = get_object_or_404(Report, pk=pk)

    if report.status != Report.Status.DRAFT:
        messages.error(
            request,
            _("Solo se pueden finalizar informes en estado borrador.")
        )
        return redirect("protocols:report_detail", pk=report.pk)

    try:
        with transaction.atomic():
            # Generate PDF
            pdf_buffer, pdf_hash = generate_report_pdf(report)
            
            # Save PDF to file
            pdf_filename = report.generate_pdf_filename()
            pdf_dir = os.path.join(settings.MEDIA_ROOT, "reports")
            os.makedirs(pdf_dir, exist_ok=True)
            
            pdf_path = os.path.join(pdf_dir, pdf_filename)
            with open(pdf_path, "wb") as f:
                f.write(pdf_buffer.getvalue())
            
            # Update report
            report.pdf_path = pdf_path
            report.pdf_hash = pdf_hash
            report.finalize()
            
            # Send email notification with PDF attachment
            _send_report_ready_notification(report, pdf_path)
            
            messages.success(
                request,
                _("Informe finalizado exitosamente. El PDF ha sido generado y enviado por email.")
            )
            return redirect("protocols:report_detail", pk=report.pk)
            
    except Exception as e:
        logger.error(f"Error finalizing report {report.pk}: {e}")
        messages.error(
            request,
            _("Error al finalizar el informe: %(error)s") % {"error": str(e)}
        )
        return redirect("protocols:report_edit", pk=report.pk)


@login_required
def report_pdf_view(request, pk):
    """View/download report PDF."""
    report = get_object_or_404(Report, pk=pk)

    # Check permissions
    is_owner = False
    if hasattr(request.user, "veterinarian_profile"):
        is_owner = request.user.veterinarian_profile == report.veterinarian
    
    if not (request.user.is_staff or is_owner):
        messages.error(
            request,
            _("No tiene permisos para ver este informe.")
        )
        return redirect("protocols:protocol_list")

    if not report.pdf_path or not os.path.exists(report.pdf_path):
        messages.error(
            request,
            _("El PDF del informe no está disponible. Debe finalizar el informe primero.")
        )
        return redirect("protocols:report_detail", pk=report.pk)

    try:
        return FileResponse(
            open(report.pdf_path, "rb"),
            content_type="application/pdf",
            as_attachment=False,
            filename=report.generate_pdf_filename(),
        )
    except Exception as e:
        logger.error(f"Error serving PDF for report {report.pk}: {e}")
        messages.error(
            request,
            _("Error al cargar el PDF del informe.")
        )
        return redirect("protocols:report_detail", pk=report.pk)


# =============================================================================
# REPORT SENDING VIA EMAIL
# =============================================================================


@login_required
@csrf_protect
def report_send_view(request, pk):
    """Send report via email to veterinarian."""
    if not request.user.is_staff:
        messages.error(
            request,
            _("No tiene permisos para acceder a esta función.")
        )
        return redirect("protocols:protocol_list")

    report = get_object_or_404(
        Report.objects.select_related(
            "protocol",
            "histopathologist",
            "veterinarian__user",
        ),
        pk=pk
    )

    if report.status != Report.Status.FINALIZED:
        messages.error(
            request,
            _("Solo se pueden enviar informes finalizados.")
        )
        return redirect("protocols:report_detail", pk=report.pk)

    if not report.pdf_path or not os.path.exists(report.pdf_path):
        messages.error(
            request,
            _("El PDF del informe no está disponible.")
        )
        return redirect("protocols:report_detail", pk=report.pk)

    form = ReportSendForm(
        request.POST or None,
        veterinarian_email=report.veterinarian.email,
    )

    if request.method == "POST" and form.is_valid():
        try:
            additional_email = form.cleaned_data.get("additional_email", "").strip()
            custom_message = form.cleaned_data.get("custom_message", "").strip()
            
            # Prepare email
            subject = _(
                "Informe Histopatológico - Protocolo %(number)s"
            ) % {"number": report.protocol.protocol_number}
            
            # Render email content
            html_message = render_to_string(
                "protocols/emails/report_delivery.html",
                {
                    "report": report,
                    "protocol": report.protocol,
                    "veterinarian": report.veterinarian,
                    "custom_message": custom_message,
                }
            )
            plain_message = strip_tags(html_message)
            
            # Prepare recipients
            recipients = [report.veterinarian.email]
            if additional_email:
                recipients.append(additional_email)
            
            # Create email with attachment
            email = EmailMessage(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
            )
            email.content_subtype = "html"
            email.body = html_message
            
            # Attach PDF
            with open(report.pdf_path, "rb") as f:
                email.attach(
                    report.generate_pdf_filename(),
                    f.read(),
                    "application/pdf"
                )
            
            # Send email
            email.send(fail_silently=False)
            
            # Update report status
            report.mark_as_sent(report.veterinarian.email)
            
            # Update protocol status
            if report.protocol.status != Protocol.Status.REPORT_SENT:
                report.protocol.status = Protocol.Status.REPORT_SENT
                report.protocol.save(update_fields=["status"])
            
            messages.success(
                request,
                _("Informe enviado exitosamente a %(email)s") % {"email": ", ".join(recipients)}
            )
            return redirect("protocols:report_detail", pk=report.pk)
            
        except Exception as e:
            logger.error(f"Error sending report {report.pk}: {e}")
            report.email_status = Report.EmailStatus.FAILED
            report.email_error = str(e)
            report.save(update_fields=["email_status", "email_error"])
            
            messages.error(
                request,
                _("Error al enviar el informe: %(error)s") % {"error": str(e)}
            )
            return redirect("protocols:report_send", pk=report.pk)

    context = {
        "form": form,
        "report": report,
        "protocol": report.protocol,
        "title": _("Enviar Informe - %(protocol)s") % {"protocol": report.protocol.protocol_number},
    }
    return render(request, "protocols/reports/send.html", context)

