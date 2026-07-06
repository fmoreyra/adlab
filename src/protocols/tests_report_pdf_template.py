"""
Tests for institutional report PDF template (roadmap 3.1).
"""

import re
import zlib
from datetime import date
from io import BytesIO

from django.test import TestCase
from PIL import Image as PILImage

from accounts.models import LaboratoryStaff, User, Veterinarian
from protocols.models import (
    Cassette,
    CytologySample,
    HistopathologySample,
    Protocol,
    Report,
    Slide,
)
from protocols.services.pdf_service import PDFGenerationService
from protocols.services.report_pdf_builder import (
    build_report_context,
    format_date_long_spanish,
)


def _make_signature_file(name="sig.png"):
    """Create a small signature image for PDF tests."""
    buffer = BytesIO()
    PILImage.new("RGB", (80, 40), "blue").save(buffer, format="PNG")
    buffer.seek(0)
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


def _pdf_text(pdf_buffer) -> str:
    """Extract searchable text from a ReportLab PDF buffer."""
    data = pdf_buffer.getvalue()
    parts = []

    for match in re.finditer(rb"\(([^)\\]*(?:\\.[^)\\]*)*)\)", data):
        parts.append(match.group(1).decode("latin-1", errors="ignore"))

    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        stream = match.group(1).strip()
        try:
            decoded = zlib.decompress(stream)
        except zlib.error:
            continue
        for inner in re.finditer(rb"\(([^)\\]*(?:\\.[^)\\]*)*)\)", decoded):
            parts.append(inner.group(1).decode("latin-1", errors="ignore"))

    return "".join(parts)


class ReportPDFContextTests(TestCase):
    """Unit tests for report PDF context helpers."""

    def setUp(self):
        self.veterinarian_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=self.veterinarian_user,
            last_name="Ricartes",
            first_name="Brian",
            license_number="VET-587",
            email="vet@example.com",
        )

    def test_format_date_long_spanish(self):
        """Spanish long dates match the faculty template style."""
        formatted = format_date_long_spanish(date(2025, 6, 9))
        self.assertEqual(formatted, "9 de junio de 2025")

    def test_build_report_context_histopathology(self):
        """HP context includes fixation and histopathology title."""
        protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Aves",
            breed="engorde",
            age="30 días",
            sex=Protocol.Sex.UNKNOWN,
            owner_last_name="Carnave",
            animal_identification="Lote 1",
            presumptive_diagnosis="Pool",
            submission_date=date(2025, 6, 9),
            status=Protocol.Status.READY,
            protocol_number="HP 25/587",
        )
        HistopathologySample.objects.create(
            protocol=protocol,
            veterinarian=self.veterinarian,
            material_submitted="Pool de muestras",
            preservation="formol al 10 %",
        )
        report = Report.objects.create(
            protocol=protocol,
            veterinarian=self.veterinarian,
            diagnosis="Sin hallazgos relevantes",
            report_date=date(2025, 6, 10),
        )

        context = build_report_context(report)

        self.assertTrue(context.is_histopathology)
        self.assertIn(
            "INFORME HISTOPATOLÓGICO Nº HP 25/587", context.report_title
        )
        self.assertEqual(context.location_year_line, "Esperanza, de 2025")
        self.assertIn("9 de junio de 2025", context.submission_date_line)
        self.assertIn("Pool de muestras", context.material_line)
        self.assertIn("Órganos fijados", context.preservation_line)

    def test_build_report_context_cytology(self):
        """CT context uses cytology title and omits fixation."""
        protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            breed="Mestizo",
            age="2 años",
            sex=Protocol.Sex.FEMALE,
            animal_identification="Luna",
            presumptive_diagnosis="Masa",
            submission_date=date(2025, 7, 1),
            status=Protocol.Status.READY,
            protocol_number="CT 26/001",
        )
        CytologySample.objects.create(
            protocol=protocol,
            veterinarian=self.veterinarian,
            sampling_site="Masa cutánea",
            technique_used="PAAF",
        )
        report = Report.objects.create(
            protocol=protocol,
            veterinarian=self.veterinarian,
            diagnosis="Células inflamatorias",
            report_date=date(2025, 7, 2),
        )

        context = build_report_context(report)

        self.assertFalse(context.is_histopathology)
        self.assertIn("INFORME CITOLÓGICO Nº CT 26/001", context.report_title)
        self.assertIsNone(context.preservation_line)
        self.assertIn("Masa cutánea", context.material_line)


class InstitutionalReportPDFTests(TestCase):
    """Integration tests for institutional PDF layout."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
            email_verified=True,
        )
        self.laboratory_staff = LaboratoryStaff.objects.create(
            user=self.staff_user,
            last_name="Canal",
            first_name="Ana María",
            license_number="MP-999",
            can_create_reports=True,
            position="Patóloga",
        )
        self.laboratory_staff.signature_image.save(
            "sig.png", _make_signature_file(), save=True
        )

        self.veterinarian_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=self.veterinarian_user,
            last_name="Ricartes",
            first_name="Brian",
            license_number="VET-587",
            email="vet@example.com",
        )

        self.hp_protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            breed="Labrador",
            age="5 años",
            sex=Protocol.Sex.MALE,
            animal_identification="Max",
            presumptive_diagnosis="Masa",
            submission_date=date(2025, 6, 9),
            status=Protocol.Status.READY,
            protocol_number="HP 24/099",
        )
        self.hp_sample = HistopathologySample.objects.create(
            protocol=self.hp_protocol,
            veterinarian=self.veterinarian,
            material_submitted="Biopsia cutánea",
            preservation="Formol 10%",
        )
        self.cassette = Cassette.objects.create(
            histopathology_sample=self.hp_sample,
            codigo_cassette="HP 24/099-C1",
            material_incluido="Piel",
        )
        Slide.objects.create(
            protocol=self.hp_protocol,
            codigo_portaobjetos="HP 24/099-S1",
            tecnica_coloracion="Hematoxilina-Eosina",
        )
        self.hp_report = Report.objects.create(
            protocol=self.hp_protocol,
            laboratory_staff=self.laboratory_staff,
            veterinarian=self.veterinarian,
            macroscopic_observations="Masa ulcerada",
            microscopic_observations="Infiltrado linfoplasmocitario",
            diagnosis="Dermatitis crónica",
            comments="Seguimiento clínico",
            recommendations="Control en 30 días",
            status=Report.Status.FINALIZED,
        )

        self.ct_protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            veterinarian=self.veterinarian,
            species="Felino",
            breed="Siames",
            age="3 años",
            sex=Protocol.Sex.FEMALE,
            animal_identification="Mishi",
            presumptive_diagnosis="Masa",
            submission_date=date(2025, 7, 1),
            status=Protocol.Status.READY,
            protocol_number="CT 26/001",
        )
        CytologySample.objects.create(
            protocol=self.ct_protocol,
            veterinarian=self.veterinarian,
            sampling_site="Masa abdominal",
            technique_used="PAAF",
        )
        self.ct_report = Report.objects.create(
            protocol=self.ct_protocol,
            laboratory_staff=self.laboratory_staff,
            veterinarian=self.veterinarian,
            diagnosis="Proceso inflamatorio",
            status=Report.Status.FINALIZED,
        )

    def test_histopathology_pdf_contains_institutional_sections(self):
        """HP PDF includes banners metadata and structured sections."""
        pdf_buffer, pdf_hash = PDFGenerationService().generate_report_pdf(
            self.hp_report
        )
        text = _pdf_text(pdf_buffer)

        self.assertGreater(len(pdf_buffer.getvalue()), 1000)
        self.assertEqual(len(pdf_hash), 64)
        self.assertIn("LABORATORIO DE ANATOM", text)
        self.assertIn("INFORME HISTOPATOL", text)
        self.assertIn("RESULTADOS", text)
        self.assertIn("OBSERVACIONES", text)
        self.assertIn("Dermatitis cr", text)
        self.assertIn("Facultad de Ciencias Veterinarias", text)
        self.assertIn("Hematoxilina-Eosina", text)

    def test_cytology_pdf_uses_cytology_title(self):
        """CT PDF uses cytology title and skips fixation line."""
        pdf_buffer, _ = PDFGenerationService().generate_report_pdf(
            self.ct_report
        )
        text = _pdf_text(pdf_buffer)

        self.assertIn("INFORME CITOL", text)
        self.assertNotIn("INFORME HISTOPATOL", text)
        self.assertIn("Masa abdominal", text)
        self.assertIn("Diff-Quick", text)

    def test_pdf_requires_signature(self):
        """Unsigned reports cannot be exported to PDF."""
        unsigned_staff = LaboratoryStaff.objects.create(
            user=User.objects.create_user(
                email="unsigned@example.com",
                username="unsigned",
                password="testpass123",
                role=User.Role.PERSONAL_LAB,
                is_staff=True,
                email_verified=True,
            ),
            last_name="Sin",
            first_name="Firma",
            license_number="MP-000",
            can_create_reports=True,
        )
        report = Report.objects.create(
            protocol=self.ct_protocol,
            laboratory_staff=unsigned_staff,
            veterinarian=self.veterinarian,
            diagnosis="Pendiente",
            status=Report.Status.FINALIZED,
        )

        from protocols.services.pdf_exceptions import PDFGenerationError

        with self.assertRaises(PDFGenerationError):
            PDFGenerationService().generate_report_pdf(report)
