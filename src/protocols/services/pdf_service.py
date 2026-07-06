"""
PDF generation service for work orders and reports.
"""

import hashlib
import io
import logging
from typing import Tuple

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
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

from protocols.services.pdf_exceptions import PDFGenerationError
from protocols.services.report_pdf_builder import ReportPDFBuilder

__all__ = ["PDFGenerationError", "PDFGenerationService"]

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
        Generate PDF for a report using the institutional ReportLab builder.
        Returns tuple of (pdf_buffer, pdf_hash).
        """
        buffer = io.BytesIO()
        ReportPDFBuilder(report).build(buffer)

        pdf_content = buffer.getvalue()
        pdf_hash = hashlib.sha256(pdf_content).hexdigest()

        buffer.seek(0)
        return buffer, pdf_hash

    def persist_report_pdf(self, report) -> Tuple[str, str]:
        """
        Generate a report PDF and save it to default storage (Garage/S3 or media).

        Args:
            report: Report instance

        Returns:
            Tuple of (storage_path, sha256_hash)

        Raises:
            PDFGenerationError: If PDF generation fails
        """
        buffer, pdf_hash = self.generate_report_pdf(report)
        filename = report.generate_pdf_filename()
        storage_name = f"reports/{report.pk}/{filename}"

        if default_storage.exists(storage_name):
            default_storage.delete(storage_name)

        saved_path = default_storage.save(
            storage_name,
            ContentFile(buffer.getvalue()),
        )
        report.pdf_path = saved_path
        report.pdf_hash = pdf_hash
        report.save(update_fields=["pdf_path", "pdf_hash"])
        return saved_path, pdf_hash
