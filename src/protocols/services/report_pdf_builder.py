"""
Institutional report PDF layout (roadmap 3.1).

Recreates the faculty Word template in ReportLab using static banner assets.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from xml.sax.saxutils import escape

from django.contrib.staticfiles import finders
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from protocols.models import Protocol, Slide
from protocols.services.pdf_exceptions import PDFGenerationError
from protocols.services.report_image_service import ReportImageService
from protocols.services.report_pdf_fonts import register_report_fonts

logger = logging.getLogger(__name__)

LABORATORY_NAME = "LABORATORIO DE ANATOMÍA PATOLÓGICA"
LABORATORY_LOCATION = "Esperanza"
INSTITUTION_LINE_1 = "Laboratorio de Anatomía Patológica"
INSTITUTION_LINE_2 = "Facultad de Ciencias Veterinarias"

HEADER_BANNER_STATIC = "images/reports/header_banner.png"
FOOTER_BANNER_STATIC = "images/reports/footer_banner.png"

SPANISH_MONTHS = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)

PAGE_WIDTH, PAGE_HEIGHT = A4
# Match renovated Word page margins (720 twips = 0.5 in).
LEFT_MARGIN = 0.5 * inch
RIGHT_MARGIN = 0.5 * inch
# Banners sit closer to the page edge than body text (legacy PDF look).
BANNER_SIDE_MARGIN = 0.2 * inch
# Leave a small marked gap between the header rule and the lab title.
TOP_MARGIN = 1.22 * inch
BOTTOM_MARGIN = 0.85 * inch


@dataclass(frozen=True)
class ReportPDFContext:
    """Resolved display values for a report PDF."""

    report_title: str
    location_year_line: str
    submission_date_line: str
    material_line: Optional[str]
    animal_line: str
    owner_line: Optional[str]
    veterinarian_line: str
    preservation_line: Optional[str]
    staining_line: Optional[str]
    is_histopathology: bool


def format_date_long_spanish(value) -> str:
    """Format a date as ``09 de junio de 2025``."""
    month_name = SPANISH_MONTHS[value.month - 1]
    return f"{value.day} de {month_name} de {value.year}"


def format_report_title_number(protocol: Protocol) -> str:
    """Return the protocol number as stored for the PDF title."""
    return protocol.protocol_number or "-"


def protocol_uses_cassette_observations(protocol: Protocol) -> bool:
    """Return whether cassette observation blocks belong on the report PDF."""
    if protocol.analysis_type != Protocol.AnalysisType.HISTOPATHOLOGY:
        return False

    return getattr(protocol, "histopathology_sample", None) is not None


def _resolve_staining_summary(protocol: Protocol) -> str:
    """Collect unique slide staining techniques for the protocol."""
    techniques = sorted(
        {
            technique.strip()
            for technique in Slide.objects.filter(
                protocol=protocol
            ).values_list("tecnica_coloracion", flat=True)
            if technique and technique.strip()
        }
    )
    if techniques:
        return ", ".join(techniques)

    if protocol.analysis_type == Protocol.AnalysisType.CYTOLOGY:
        return "Diff-Quick"

    return "Hematoxilina-Eosina"


def _build_animal_line(protocol: Protocol) -> str:
    """Build a single-line animal description for the PDF header."""
    parts = [
        protocol.species,
        protocol.breed,
        protocol.animal_category,
        protocol.age,
        protocol.get_sex_display() if protocol.sex else "",
    ]
    cleaned = [part.strip() for part in parts if part and str(part).strip()]
    if not cleaned:
        return "-"

    line = ", ".join(cleaned)
    if not line.endswith("."):
        line = f"{line}."
    return line


def _build_material_line(protocol: Protocol) -> Optional[str]:
    """Return the submitted material line for HP or CT protocols."""
    if protocol.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY:
        sample = getattr(protocol, "histopathology_sample", None)
        if not sample:
            return None
        return sample.material_submitted.strip()

    sample = getattr(protocol, "cytology_sample", None)
    if not sample:
        return None

    parts = [sample.sampling_site.strip(), sample.technique_used.strip()]
    cleaned = [part for part in parts if part]
    return " — ".join(cleaned) if cleaned else None


def _build_preservation_line(protocol: Protocol) -> Optional[str]:
    """Return fixation/preservation text for histopathology reports."""
    if protocol.analysis_type != Protocol.AnalysisType.HISTOPATHOLOGY:
        return None

    sample = getattr(protocol, "histopathology_sample", None)
    if not sample or not sample.preservation:
        return None

    preservation = sample.preservation.strip().rstrip(".")
    return f"Órganos fijados en {preservation.lower()}."


def build_report_context(report) -> ReportPDFContext:
    """
    Build display context for institutional report PDF generation.

    Args:
        report: Report instance with related protocol loaded

    Returns:
        ReportPDFContext: Resolved header metadata and flags
    """
    protocol = report.protocol
    is_hp = protocol.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY
    title_prefix = "INFORME HISTOPATOLÓGICO" if is_hp else "INFORME CITOLÓGICO"
    report_title = f"{title_prefix} Nº {format_report_title_number(protocol)}"
    # Faculty template uses the report issue / finalization date here.
    location_year_line = f"{LABORATORY_LOCATION}, {format_date_long_spanish(report.report_date)}"
    submission_date_line = (
        f"Fecha de remisión: "
        f"{format_date_long_spanish(protocol.submission_date)}"
    )

    owner_name = protocol.get_owner_full_name()
    owner_line = f"Propietario: {owner_name}" if owner_name else None

    vet = report.veterinarian
    vet_name = vet.get_full_name().strip()
    veterinarian_line = f"Profesional comitente: MV {vet_name}"
    if vet.license_number:
        veterinarian_line = f"{veterinarian_line} {vet.license_number}".strip()

    material = _build_material_line(protocol)
    material_line = f"Material remitido: {material}." if material else None

    staining = _resolve_staining_summary(protocol)
    staining_line = f"Tinción realizada: {staining}."

    return ReportPDFContext(
        report_title=report_title,
        location_year_line=location_year_line,
        submission_date_line=submission_date_line,
        material_line=material_line,
        animal_line=f"Datos del animal: {_build_animal_line(protocol)}",
        owner_line=owner_line,
        veterinarian_line=veterinarian_line,
        preservation_line=_build_preservation_line(protocol),
        staining_line=staining_line,
        is_histopathology=is_hp,
    )


def _resolve_banner_path(static_path: str) -> Optional[str]:
    """Locate a banner image via repo assets (dev) or staticfiles."""
    # Prefer versioned assets in the repo so local volume mounts win over
    # the image-baked /public copy used by STATICFILES_DIRS in Docker.
    repo_path = (
        Path(__file__).resolve().parents[3] / "assets" / "static" / static_path
    )
    if repo_path.is_file():
        return str(repo_path)

    found = finders.find(static_path)
    if found:
        return found

    logger.warning("Report PDF banner not found: %s", static_path)
    return None


def _paragraph_text(text: str) -> str:
    """Escape plain text for ReportLab Paragraph markup."""
    return escape(text).replace("\n", "<br/>")


def _labeled_meta_markup(label: str, value: str) -> str:
    """
    Build ReportLab markup with a bold label and regular value.

    Args:
        label: Field title without trailing colon
        value: Field body text

    Returns:
        str: Escaped Paragraph markup
    """
    return f"<b>{escape(label)}:</b> {_paragraph_text(value)}"


def _meta_line_markup(line: str) -> str:
    """
    Bold the label before the first ``: `` in a metadata line.

    Args:
        line: Plain ``Label: value`` text, or a full sentence without a label

    Returns:
        str: Escaped Paragraph markup
    """
    if ": " not in line:
        return _paragraph_text(line)

    label, value = line.split(": ", 1)
    return _labeled_meta_markup(label, value)


class ReportPDFBuilder:
    """Build institutional pathology report PDFs with header/footer banners."""

    def __init__(self, report):
        self.report = report
        self.context = build_report_context(report)
        self.header_path = _resolve_banner_path(HEADER_BANNER_STATIC)
        self.footer_path = _resolve_banner_path(FOOTER_BANNER_STATIC)
        self._styles = self._build_styles()

    def _build_styles(self):
        """Create paragraph styles matching the faculty Calibri template."""
        font_regular, font_bold = register_report_fonts()
        base = getSampleStyleSheet()
        return {
            "lab_title": ParagraphStyle(
                "LabTitle",
                parent=base["Normal"],
                fontName=font_bold,
                fontSize=14,
                alignment=TA_CENTER,
                spaceAfter=4,
            ),
            "report_title": ParagraphStyle(
                "ReportTitle",
                parent=base["Normal"],
                fontName=font_bold,
                fontSize=14,
                alignment=TA_CENTER,
                spaceAfter=12,
            ),
            "meta_bold": ParagraphStyle(
                "MetaBold",
                parent=base["Normal"],
                fontName=font_bold,
                fontSize=12,
                spaceAfter=6,
            ),
            "meta": ParagraphStyle(
                "Meta",
                parent=base["Normal"],
                fontName=font_regular,
                fontSize=12,
                spaceAfter=6,
            ),
            "section": ParagraphStyle(
                "Section",
                parent=base["Normal"],
                fontName=font_bold,
                fontSize=12,
                spaceBefore=8,
                spaceAfter=6,
            ),
            "subsection": ParagraphStyle(
                "Subsection",
                parent=base["Normal"],
                fontName=font_bold,
                fontSize=11,
                spaceBefore=6,
                spaceAfter=4,
            ),
            "body": ParagraphStyle(
                "Body",
                parent=base["Normal"],
                fontName=font_regular,
                fontSize=12,
                spaceAfter=8,
            ),
            "diagnosis": ParagraphStyle(
                "Diagnosis",
                parent=base["Normal"],
                fontName=font_bold,
                fontSize=12,
                spaceAfter=10,
            ),
            "caption": ParagraphStyle(
                "Caption",
                parent=base["Normal"],
                fontName=font_regular,
                fontSize=9,
                textColor=colors.HexColor("#555555"),
                spaceAfter=12,
            ),
            "signature": ParagraphStyle(
                "Signature",
                parent=base["Normal"],
                fontName=font_bold,
                fontSize=12,
                alignment=TA_RIGHT,
                spaceAfter=2,
            ),
        }

    def _draw_banner(
        self,
        canvas,
        image_path: Optional[str],
        y_position: float,
        usable_width: float,
        x_position: float,
    ) -> None:
        """Draw a full-width banner image at the given vertical position."""
        if not image_path:
            return

        try:
            reader = ImageReader(image_path)
            img_width, img_height = reader.getSize()
            scale = usable_width / img_width
            draw_height = img_height * scale
            canvas.drawImage(
                image_path,
                x_position,
                y_position,
                width=usable_width,
                height=draw_height,
                mask="auto",
                preserveAspectRatio=True,
            )
        except Exception as exc:
            logger.warning(
                "Could not draw report banner %s: %s", image_path, exc
            )

    def _draw_page_decorations(self, canvas, doc) -> None:
        """Render header and footer banners on every page."""
        canvas.saveState()
        banner_width = PAGE_WIDTH - (2 * BANNER_SIDE_MARGIN)

        if self.header_path:
            try:
                reader = ImageReader(self.header_path)
                img_width, img_height = reader.getSize()
                scale = banner_width / img_width
                header_height = img_height * scale
                header_y = PAGE_HEIGHT - header_height - 8
                self._draw_banner(
                    canvas,
                    self.header_path,
                    header_y,
                    banner_width,
                    BANNER_SIDE_MARGIN,
                )
            except Exception as exc:
                logger.warning("Could not render header banner: %s", exc)

        if self.footer_path:
            try:
                self._draw_banner(
                    canvas,
                    self.footer_path,
                    14,
                    banner_width,
                    BANNER_SIDE_MARGIN,
                )
            except Exception as exc:
                logger.warning("Could not render footer banner: %s", exc)

        canvas.restoreState()

    def _append_metadata_lines(self, elements: List) -> None:
        """Add institutional header and metadata block."""
        styles = self._styles
        # Extra breathing room under the banner rule (complements TOP_MARGIN).
        elements.append(Spacer(1, 6))
        elements.append(
            Paragraph(_paragraph_text(LABORATORY_NAME), styles["lab_title"])
        )
        elements.append(
            Paragraph(
                _paragraph_text(self.context.location_year_line),
                styles["lab_title"],
            )
        )
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(
            Paragraph(
                _paragraph_text(self.context.report_title),
                styles["report_title"],
            )
        )
        metadata_lines = [
            self.context.submission_date_line,
            self.context.material_line,
            self.context.animal_line,
            self.context.owner_line,
            self.context.veterinarian_line,
            self.context.preservation_line,
            self.context.staining_line,
        ]
        for line in metadata_lines:
            if line:
                elements.append(
                    Paragraph(_meta_line_markup(line), styles["meta"])
                )

        elements.append(Spacer(1, 0.1 * inch))

    def _append_results_section(self, elements: List) -> None:
        """Add RESULTADOS block with structured clinical content."""
        styles = self._styles
        report = self.report

        elements.append(Paragraph("RESULTADOS:", styles["section"]))

        if report.macroscopic_observations:
            elements.append(
                Paragraph("Descripción macroscópica", styles["subsection"])
            )
            elements.append(
                Paragraph(
                    _paragraph_text(report.macroscopic_observations),
                    styles["body"],
                )
            )

        if report.microscopic_observations:
            elements.append(
                Paragraph("Descripción microscópica", styles["subsection"])
            )
            elements.append(
                Paragraph(
                    _paragraph_text(report.microscopic_observations),
                    styles["body"],
                )
            )

        if protocol_uses_cassette_observations(report.protocol):
            cassette_observations = report.cassette_observations.order_by(
                "order", "cassette__codigo_cassette"
            )
            if cassette_observations.exists():
                elements.append(
                    Paragraph(
                        "Observaciones por cassette", styles["subsection"]
                    )
                )
                for obs in cassette_observations:
                    cassette_title = f"Cassette {obs.cassette.codigo_cassette}"
                    elements.append(
                        Paragraph(
                            _paragraph_text(cassette_title),
                            styles["subsection"],
                        )
                    )
                    elements.append(
                        Paragraph(
                            _paragraph_text(obs.observations), styles["body"]
                        )
                    )
                    if obs.partial_diagnosis:
                        elements.append(
                            Paragraph(
                                _paragraph_text(
                                    f"Diagnóstico: {obs.partial_diagnosis}"
                                ),
                                styles["body"],
                            )
                        )

        report_images = report.images.filter(include_in_pdf=True).order_by(
            "order", "created_at"
        )
        if report_images.exists():
            elements.append(
                Paragraph("Imágenes microscópicas", styles["subsection"])
            )
            for report_image in report_images:
                if not report_image.image:
                    continue
                try:
                    img_buffer = ReportImageService.open_for_pdf(report_image)
                    reader = ImageReader(img_buffer)
                    img_w, img_h = reader.getSize()
                    max_w, max_h = 4.5 * inch, 3.5 * inch
                    scale = min(max_w / img_w, max_h / img_h, 1.0)
                    img_buffer.seek(0)
                    elements.append(
                        Image(
                            img_buffer,
                            width=img_w * scale,
                            height=img_h * scale,
                        )
                    )
                except Exception as exc:
                    logger.warning(
                        "Could not load report image %s: %s",
                        report_image.pk,
                        exc,
                    )
                    continue

                caption_parts = []
                if report_image.cassette:
                    caption_parts.append(
                        f"Cassette {report_image.cassette.codigo_cassette}"
                    )
                if report_image.magnification:
                    caption_parts.append(report_image.magnification)
                if report_image.technique:
                    caption_parts.append(report_image.technique)
                if report_image.description:
                    caption_parts.append(report_image.description)

                if caption_parts:
                    elements.append(
                        Paragraph(
                            _paragraph_text(" — ".join(caption_parts)),
                            styles["caption"],
                        )
                    )

        elements.append(Paragraph("Diagnóstico", styles["subsection"]))
        elements.append(
            Paragraph(_paragraph_text(report.diagnosis), styles["diagnosis"])
        )

    def _append_observations_section(self, elements: List) -> None:
        """Add OBSERVACIONES block for comments and recommendations."""
        styles = self._styles
        report = self.report

        if not report.comments and not report.recommendations:
            return

        elements.append(Paragraph("OBSERVACIONES:", styles["section"]))

        if report.comments:
            elements.append(Paragraph("Comentarios", styles["subsection"]))
            elements.append(
                Paragraph(_paragraph_text(report.comments), styles["body"])
            )

        if report.recommendations:
            elements.append(Paragraph("Recomendaciones", styles["subsection"]))
            elements.append(
                Paragraph(
                    _paragraph_text(report.recommendations), styles["body"]
                )
            )

    def _append_signature_block(self, elements: List) -> None:
        """Add right-aligned signature image and institutional signer lines."""
        report = self.report
        signer = report.get_signer()
        if not signer:
            raise PDFGenerationError(
                "El informe no tiene un profesional asignado para firmar."
            )

        if not report.signer_has_signature():
            raise PDFGenerationError(
                "El profesional asignado no tiene firma digital cargada."
            )

        elements.append(Spacer(1, 0.4 * inch))
        styles = self._styles

        if signer.signature_image:
            try:
                with signer.signature_image.open("rb") as img_file:
                    sig_data = img_file.read()
                sig_buffer = io.BytesIO(sig_data)
                sig_image = Image(sig_buffer, width=2 * inch, height=1 * inch)
                content_width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
                sig_table = Table(
                    [[sig_image]],
                    colWidths=[content_width],
                )
                sig_table.setStyle(
                    TableStyle(
                        [
                            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ]
                    )
                )
                elements.append(sig_table)
            except Exception as exc:
                logger.warning("Could not load signature image: %s", exc)

        signature_lines = [signer.get_formal_name()]
        if signer.license_number:
            signature_lines.append(f"Mat. {signer.license_number}")
        if signer.position:
            signature_lines.append(signer.position)
        signature_lines.extend([INSTITUTION_LINE_1, INSTITUTION_LINE_2])

        for line in signature_lines:
            elements.append(
                Paragraph(_paragraph_text(line), styles["signature"])
            )

    def build(self, buffer: io.BytesIO) -> None:
        """
        Render the report PDF into the provided buffer.

        Args:
            buffer: Writable BytesIO buffer
        """
        doc = BaseDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=LEFT_MARGIN,
            rightMargin=RIGHT_MARGIN,
            topMargin=TOP_MARGIN,
            bottomMargin=BOTTOM_MARGIN,
        )
        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id="report-body",
        )
        template = PageTemplate(
            id="institutional-report",
            frames=[frame],
            onPage=self._draw_page_decorations,
        )
        doc.addPageTemplates([template])

        elements: List = []
        self._append_metadata_lines(elements)
        self._append_results_section(elements)
        self._append_observations_section(elements)
        self._append_signature_block(elements)

        doc.build(elements)
