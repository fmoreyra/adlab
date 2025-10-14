"""
PDF generation service for work orders and reports.
"""

import hashlib
import io
import logging
import os
from typing import Tuple

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

logger = logging.getLogger(__name__)


class PDFGenerationService:
    """
    Service class for generating PDF documents.

    This service encapsulates PDF generation logic and provides a clean
    interface for creating various types of PDF documents.
    """

    def generate_workorder_pdf(self, work_order) -> io.BytesIO:
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

    def generate_report_pdf(self, report) -> Tuple[io.BytesIO, str]:
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
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=16,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=30,
            alignment=1,  # Center
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#333333"),
            spaceAfter=12,
            spaceBefore=12,
        )

        normal_style = styles["Normal"]

        # Title
        elements.append(Paragraph("INFORME HISTOPATOLÓGICO", title_style))
        elements.append(Spacer(1, 0.2 * inch))

        # Protocol information
        protocol = report.protocol
        protocol_data = [
            ["Protocolo:", protocol.protocol_number or "-"],
            ["Fecha de Informe:", report.report_date.strftime("%d/%m/%Y")],
            ["Versión:", str(report.version)],
        ]

        protocol_table = Table(protocol_data, colWidths=[2 * inch, 4 * inch])
        protocol_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONT", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(protocol_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Patient information
        elements.append(Paragraph("DATOS DEL PACIENTE", heading_style))
        patient_data = [
            ["Especie:", protocol.species],
            ["Raza:", protocol.breed or "-"],
            ["Edad:", protocol.age or "-"],
            ["Sexo:", protocol.get_sex_display()],
            ["Identificación:", protocol.animal_identification or "-"],
        ]

        patient_table = Table(patient_data, colWidths=[2 * inch, 4 * inch])
        patient_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONT", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(patient_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Veterinarian information
        elements.append(Paragraph("VETERINARIO SOLICITANTE", heading_style))
        vet = report.veterinarian
        vet_data = [
            ["Nombre:", vet.get_full_name()],
            ["Matrícula:", vet.license_number],
            ["Email:", vet.email],
            ["Teléfono:", vet.phone or "-"],
        ]

        vet_table = Table(vet_data, colWidths=[2 * inch, 4 * inch])
        vet_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONT", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(vet_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Macroscopic observations
        if report.macroscopic_observations:
            elements.append(
                Paragraph("DESCRIPCIÓN MACROSCÓPICA", heading_style)
            )
            elements.append(
                Paragraph(report.macroscopic_observations, normal_style)
            )
            elements.append(Spacer(1, 0.2 * inch))

        # Microscopic observations
        if report.microscopic_observations:
            elements.append(
                Paragraph("DESCRIPCIÓN MICROSCÓPICA", heading_style)
            )
            elements.append(
                Paragraph(report.microscopic_observations, normal_style)
            )
            elements.append(Spacer(1, 0.2 * inch))

        # Cassette observations
        cassette_observations = report.cassette_observations.order_by(
            "order", "cassette__codigo_cassette"
        )
        if cassette_observations.exists():
            elements.append(
                Paragraph("OBSERVACIONES POR CASSETTE", heading_style)
            )
            for obs in cassette_observations:
                cassette_title = f"Cassette {obs.cassette.codigo_cassette}"
                elements.append(
                    Paragraph(
                        cassette_title,
                        ParagraphStyle(
                            "CassetteTitle",
                            parent=styles["Heading3"],
                            fontSize=10,
                            textColor=colors.HexColor("#555555"),
                            spaceAfter=6,
                            spaceBefore=6,
                        ),
                    )
                )
                elements.append(Paragraph(obs.observations, normal_style))
                if obs.partial_diagnosis:
                    elements.append(
                        Paragraph(
                            f"<b>Diagnóstico:</b> {obs.partial_diagnosis}",
                            normal_style,
                        )
                    )
                elements.append(Spacer(1, 0.15 * inch))

        # Diagnosis
        elements.append(Paragraph("DIAGNÓSTICO", heading_style))
        elements.append(
            Paragraph(
                report.diagnosis,
                ParagraphStyle(
                    "Diagnosis",
                    parent=normal_style,
                    fontSize=11,
                    textColor=colors.HexColor("#000000"),
                    spaceAfter=12,
                    fontName="Helvetica-Bold",
                ),
            )
        )

        # Comments
        if report.comments:
            elements.append(Paragraph("COMENTARIOS", heading_style))
            elements.append(Paragraph(report.comments, normal_style))
            elements.append(Spacer(1, 0.2 * inch))

        # Recommendations
        if report.recommendations:
            elements.append(Paragraph("RECOMENDACIONES", heading_style))
            elements.append(Paragraph(report.recommendations, normal_style))
            elements.append(Spacer(1, 0.2 * inch))

        # Signature
        elements.append(Spacer(1, 0.5 * inch))
        histopath = report.histopathologist

        # Add signature image if available
        if histopath.signature_image and os.path.exists(
            histopath.signature_image.path
        ):
            try:
                sig_img = Image(
                    histopath.signature_image.path,
                    width=2 * inch,
                    height=1 * inch,
                )
                elements.append(sig_img)
            except Exception as e:
                logger.warning(f"Could not load signature image: {e}")

        signature_data = [
            [histopath.get_formal_name()],
            [f"Mat. {histopath.license_number}"],
        ]
        if histopath.position:
            signature_data.append([histopath.position])

        signature_table = Table(signature_data, colWidths=[4 * inch])
        signature_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGNMENT", (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        elements.append(signature_table)

        # Build PDF
        doc.build(elements)

        # Get PDF content and calculate hash
        pdf_content = buffer.getvalue()
        pdf_hash = hashlib.sha256(pdf_content).hexdigest()

        buffer.seek(0)
        return buffer, pdf_hash
