"""
Tests for report signature requirements and lab staff signature upload.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import LaboratoryStaff, Veterinarian
from accounts.report_access import user_requires_report_signature
from protocols.models import Protocol, Report
from protocols.services.pdf_service import (
    PDFGenerationError,
    PDFGenerationService,
)

User = get_user_model()

MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


class ReportSignatureAccessTest(TestCase):
    """Test signature enforcement for pathology reports."""

    def setUp(self):
        self.lab_user = User.objects.create_user(
            email="lab@example.com",
            username="lab@example.com",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            email_verified=True,
        )
        self.veterinarian_user = User.objects.create_user(
            email="vet@example.com",
            username="vet@example.com",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=self.veterinarian_user,
            first_name="Ana",
            last_name="Lopez",
            license_number="VET-001",
            cuil_cuit="20-12345678-9",
        )
        self.lab_staff = LaboratoryStaff.objects.create(
            user=self.lab_user,
            first_name="Laura",
            last_name="Lab",
            license_number="LAB-001",
            can_create_reports=True,
            is_active=True,
        )
        self.protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            animal_identification="Rex",
            presumptive_diagnosis="Masa",
            submission_date=date.today(),
            status=Protocol.Status.READY,
            protocol_number="HP 26/001",
        )
        self.report = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            laboratory_staff=self.lab_staff,
            diagnosis="Diagnóstico de prueba",
            status=Report.Status.FINALIZED,
        )

    def test_user_requires_report_signature_without_image(self):
        """Lab staff with report permission but no signature must upload one."""
        self.assertTrue(user_requires_report_signature(self.lab_user))

    def test_user_requires_report_signature_with_image(self):
        """Lab staff with signature uploaded can work on reports."""
        self.lab_staff.signature_image = SimpleUploadedFile(
            "sig.png", MINIMAL_PNG, content_type="image/png"
        )
        self.lab_staff.save()
        self.assertFalse(user_requires_report_signature(self.lab_user))

    def test_report_create_redirects_without_signature(self):
        """Creating a report redirects to signature upload when missing."""
        self.client.login(email="lab@example.com", password="testpass123")
        response = self.client.get(
            reverse(
                "protocols:report_create",
                kwargs={"protocol_id": self.protocol.pk},
            )
        )
        self.assertRedirects(response, reverse("accounts:lab_staff_signature"))

    def test_report_pdf_fails_without_signer(self):
        """PDF generation raises a clear error when no signer is assigned."""
        self.report.laboratory_staff = None
        self.report.save(update_fields=["laboratory_staff"])

        with self.assertRaises(PDFGenerationError):
            PDFGenerationService().generate_report_pdf(self.report)

    def test_lab_staff_signature_form_saves_image(self):
        """Signature upload form stores the image on the profile."""
        image = SimpleUploadedFile(
            "sig.png", MINIMAL_PNG, content_type="image/png"
        )
        self.client.login(email="lab@example.com", password="testpass123")
        response = self.client.post(
            reverse("accounts:lab_staff_signature"),
            {"signature_image": image},
            format="multipart",
        )
        self.assertEqual(response.status_code, 302)
        self.lab_staff.refresh_from_db()
        self.assertTrue(self.lab_staff.has_signature())
