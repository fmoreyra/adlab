"""
ReportLab font registration for institutional report PDFs.

Calibri is Microsoft-proprietary and cannot be redistributed. Carlito is the
SIL Open Font License metric-compatible substitute (same role LibreOffice
uses as Calibri replacement).
"""

from __future__ import annotations

import logging
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

FONT_FAMILY = "Carlito"
FONT_REGULAR = "Carlito"
FONT_BOLD = "Carlito-Bold"
FONT_ITALIC = "Carlito-Italic"
FONT_BOLD_ITALIC = "Carlito-BoldItalic"

_REGISTERED = False

_FONT_FILES = {
    FONT_REGULAR: "Carlito-Regular.ttf",
    FONT_BOLD: "Carlito-Bold.ttf",
    FONT_ITALIC: "Carlito-Italic.ttf",
    FONT_BOLD_ITALIC: "Carlito-BoldItalic.ttf",
}


def _fonts_dir() -> Path:
    """Return the repo ``assets/fonts/carlito`` directory."""
    return Path(__file__).resolve().parents[3] / "assets" / "fonts" / "carlito"


def register_report_fonts() -> tuple[str, str]:
    """
    Register Carlito TTF faces for ReportLab, once per process.

    Returns:
        tuple[str, str]: ``(regular_font_name, bold_font_name)``. Falls back
        to Helvetica / Helvetica-Bold if Carlito files are missing.
    """
    global _REGISTERED

    if _REGISTERED and FONT_REGULAR in pdfmetrics.getRegisteredFontNames():
        return FONT_REGULAR, FONT_BOLD

    fonts_dir = _fonts_dir()
    missing = [
        filename
        for filename in _FONT_FILES.values()
        if not (fonts_dir / filename).is_file()
    ]
    if missing:
        logger.warning(
            "Carlito fonts missing under %s (%s); falling back to Helvetica",
            fonts_dir,
            ", ".join(missing),
        )
        return "Helvetica", "Helvetica-Bold"

    try:
        for font_name, filename in _FONT_FILES.items():
            if font_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(
                    TTFont(font_name, str(fonts_dir / filename))
                )
        pdfmetrics.registerFontFamily(
            FONT_FAMILY,
            normal=FONT_REGULAR,
            bold=FONT_BOLD,
            italic=FONT_ITALIC,
            boldItalic=FONT_BOLD_ITALIC,
        )
        _REGISTERED = True
        return FONT_REGULAR, FONT_BOLD
    except Exception:
        logger.exception(
            "Failed to register Carlito fonts; falling back to Helvetica"
        )
        return "Helvetica", "Helvetica-Bold"
