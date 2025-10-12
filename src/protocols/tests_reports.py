"""
Tests for report generation and management.
"""

from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Histopathologist, Veterinarian
from protocols.models import (
    Cassette,
    CassetteObservation,
    HistopathologySample,
    Protocol,
    Report,
)

User = get_user_model()


class ReportModelTest(TestCase):
    """Tests for Report model."""

    def setUp(self):
        """Set up test data."""
        # Create veterinarian user and profile
        vet_user = User.objects.create_user(
            username="vet@test.com",
            email="vet@test.com",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=vet_user,
            first_name="Carlos",
            last_name="Rodríguez",
            license_number="MP-12345-REPORTS",
            email="vet@test.com",
            phone="+54 342 1234567",
        )

        # Create histopathologist user and profile
        histo_user = User.objects.create_user(
            username="histo@test.com",
            email="histo@test.com",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
        )
        self.histopathologist = Histopathologist.objects.create(
            user=histo_user,
            first_name="Ana",
            last_name="López",
            license_number="MV-54321",
            position="Profesora Asociada",
            is_active=True,
        )

        # Create protocol
        self.protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            breed="Labrador",
            sex=Protocol.Sex.MALE,
            age="5 años",
            animal_identification="Max",
            presumptive_diagnosis="Tumor cutáneo",
            clinical_history="Masa en miembro anterior",
            submission_date=date.today(),
            status=Protocol.Status.READY,
        )
        self.protocol.protocol_number = "HP 24/001"
        self.protocol.save()

        # Create report
        self.report = Report.objects.create(
            protocol=self.protocol,
            histopathologist=self.histopathologist,
            veterinarian=self.veterinarian,
            macroscopic_observations="Masa de 3x2cm",
            microscopic_observations="Proliferación neoplásica",
            diagnosis="Carcinoma de células escamosas",
            status=Report.Status.DRAFT,
        )

    def test_report_creation(self):
        """Test report can be created."""
        self.assertEqual(self.report.protocol, self.protocol)
        self.assertEqual(self.report.status, Report.Status.DRAFT)
        self.assertEqual(self.report.version, 1)

    def test_report_str(self):
        """Test report string representation."""
        expected = f"Informe {self.protocol.protocol_number} - v1"
        self.assertEqual(str(self.report), expected)

    def test_report_can_edit(self):
        """Test report can be edited only when draft."""
        self.assertTrue(self.report.can_edit())
        self.report.status = Report.Status.FINALIZED
        self.report.save()
        self.assertFalse(self.report.can_edit())

    def test_report_finalize(self):
        """Test report finalization."""
        self.report.finalize()
        self.assertEqual(self.report.status, Report.Status.FINALIZED)

    def test_report_mark_as_sent(self):
        """Test marking report as sent."""
        test_email = "test@example.com"
        self.report.status = Report.Status.FINALIZED
        self.report.save()
        self.report.mark_as_sent(test_email)
        self.assertEqual(self.report.status, Report.Status.SENT)
        self.assertEqual(self.report.sent_to_email, test_email)
        self.assertEqual(self.report.email_status, Report.EmailStatus.SENT)

    def test_report_generate_pdf_filename(self):
        """Test PDF filename generation."""
        filename = self.report.generate_pdf_filename()
        self.assertIn("HP_24_001", filename)
        self.assertIn("v1", filename)
        self.assertTrue(filename.endswith(".pdf"))


class CassetteObservationModelTest(TestCase):
    """Tests for CassetteObservation model."""

    def setUp(self):
        """Set up test data."""
        # Create users and profiles
        vet_user = User.objects.create_user(
            username="vet@test.com",
            email="vet@test.com",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=vet_user,
            first_name="Carlos",
            last_name="Rodríguez",
            license_number="MP-12345-REPORTS",
            email="vet@test.com",
        )

        histo_user = User.objects.create_user(
            username="histo@test.com",
            email="histo@test.com",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
        )
        self.histopathologist = Histopathologist.objects.create(
            user=histo_user,
            first_name="Ana",
            last_name="López",
            license_number="MV-54321",
            is_active=True,
        )

        # Create protocol and sample
        self.protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            submission_date=date.today(),
            status=Protocol.Status.READY,
        )
        self.protocol.protocol_number = "HP 24/001"
        self.protocol.save()

        self.sample = HistopathologySample.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            material_submitted="Fragmento de piel - biopsia",
            number_of_containers=1,
        )

        # Create cassette
        self.cassette = Cassette.objects.create(
            histopathology_sample=self.sample,
            codigo_cassette="HP 24/001-C1",
            material_incluido="Fragmento de piel",
        )

        # Create report
        self.report = Report.objects.create(
            protocol=self.protocol,
            histopathologist=self.histopathologist,
            veterinarian=self.veterinarian,
            diagnosis="Test diagnosis",
        )

    def test_cassette_observation_creation(self):
        """Test cassette observation can be created."""
        obs = CassetteObservation.objects.create(
            report=self.report,
            cassette=self.cassette,
            observations="Proliferación neoplásica",
            partial_diagnosis="Carcinoma",
            order=1,
        )
        self.assertEqual(obs.report, self.report)
        self.assertEqual(obs.cassette, self.cassette)
        self.assertEqual(obs.order, 1)

    def test_cassette_observation_str(self):
        """Test cassette observation string representation."""
        obs = CassetteObservation.objects.create(
            report=self.report,
            cassette=self.cassette,
            observations="Test observations",
        )
        expected = f"{self.report} - {self.cassette.codigo_cassette}"
        self.assertEqual(str(obs), expected)


class ReportViewsTest(TestCase):
    """Tests for report views."""

    def setUp(self):
        """Set up test data and client."""
        self.client = Client()

        # Create veterinarian
        vet_user = User.objects.create_user(
            username="vet@test.com",
            email="vet@test.com",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=vet_user,
            first_name="Carlos",
            last_name="Rodríguez",
            license_number="MP-12345-REPORTS",
            email="vet@test.com",
        )

        # Create staff user with histopathologist profile
        staff_user = User.objects.create_user(
            username="staff@test.com",
            email="staff@test.com",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
        )
        self.histopathologist = Histopathologist.objects.create(
            user=staff_user,
            first_name="Ana",
            last_name="López",
            license_number="MV-54321",
            is_active=True,
        )

        # Create protocol
        self.protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            submission_date=date.today(),
            status=Protocol.Status.READY,
        )
        self.protocol.protocol_number = "HP 24/001"
        self.protocol.save()

    def test_report_pending_list_requires_staff(self):
        """Test that pending list requires staff permissions."""
        # Not logged in
        response = self.client.get(reverse("protocols:report_pending_list"))
        self.assertEqual(response.status_code, 302)

        # Logged in as veterinarian (not staff)
        self.client.login(username="vet@test.com", password="testpass123")
        response = self.client.get(reverse("protocols:report_pending_list"))
        self.assertEqual(response.status_code, 302)

        # Logged in as staff
        self.client.login(username="staff@test.com", password="testpass123")
        response = self.client.get(reverse("protocols:report_pending_list"))
        self.assertEqual(response.status_code, 200)

    def test_report_create_view(self):
        """Test report creation view."""
        self.client.login(username="staff@test.com", password="testpass123")
        url = reverse("protocols:report_create", args=[self.protocol.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.protocol.protocol_number)

    def test_report_create_post(self):
        """Test creating a report via POST."""
        self.client.login(username="staff@test.com", password="testpass123")
        url = reverse("protocols:report_create", args=[self.protocol.pk])
        data = {
            "histopathologist": self.histopathologist.pk,
            "macroscopic_observations": "Masa de 3x2cm",
            "microscopic_observations": "Proliferación neoplásica",
            "diagnosis": "Carcinoma de células escamosas",
            "comments": "Márgenes libres",
            "recommendations": "Control post-operatorio",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Report.objects.count(), 1)

    def test_report_detail_view(self):
        """Test report detail view."""
        report = Report.objects.create(
            protocol=self.protocol,
            histopathologist=self.histopathologist,
            veterinarian=self.veterinarian,
            diagnosis="Test diagnosis",
        )
        self.client.login(username="staff@test.com", password="testpass123")
        url = reverse("protocols:report_detail", args=[report.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, report.diagnosis)


class ReportPDFGenerationTest(TestCase):
    """Tests for PDF generation."""

    def setUp(self):
        """Set up test data."""
        # Create users and profiles
        vet_user = User.objects.create_user(
            username="vet@test.com",
            email="vet@test.com",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=vet_user,
            first_name="Carlos",
            last_name="Rodríguez",
            license_number="MP-12345-REPORTS",
            email="vet@test.com",
        )

        histo_user = User.objects.create_user(
            username="histo@test.com",
            email="histo@test.com",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
        )
        self.histopathologist = Histopathologist.objects.create(
            user=histo_user,
            first_name="Ana",
            last_name="López",
            license_number="MV-54321",
            is_active=True,
        )

        # Create protocol
        self.protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            breed="Labrador",
            sex=Protocol.Sex.MALE,
            age="5 años",
            animal_identification="Max",
            submission_date=date.today(),
            status=Protocol.Status.READY,
        )
        self.protocol.protocol_number = "HP 24/001"
        self.protocol.save()

        # Create report
        self.report = Report.objects.create(
            protocol=self.protocol,
            histopathologist=self.histopathologist,
            veterinarian=self.veterinarian,
            macroscopic_observations="Masa de 3x2cm",
            microscopic_observations="Proliferación neoplásica",
            diagnosis="Carcinoma de células escamosas",
        )

    @patch("protocols.views_reports.generate_report_pdf")
    def test_report_finalize_generates_pdf(self, mock_generate_pdf):
        """Test that finalizing report generates PDF."""
        # Mock PDF generation
        from io import BytesIO

        mock_buffer = BytesIO(b"fake pdf content")
        mock_generate_pdf.return_value = (mock_buffer, "fakehash123")

        self.client.login(username="histo@test.com", password="testpass123")
        url = reverse("protocols:report_finalize", args=[self.report.pk])
        self.client.post(url)

        # Check that PDF generation was called
        mock_generate_pdf.assert_called_once()

    def test_pdf_generation_function(self):
        """Test PDF generation function produces valid output."""
        from protocols.views_reports import generate_report_pdf

        pdf_buffer, pdf_hash = generate_report_pdf(self.report)

        # Check that PDF was generated
        self.assertIsNotNone(pdf_buffer)
        self.assertIsNotNone(pdf_hash)
        self.assertGreater(len(pdf_buffer.getvalue()), 0)
        self.assertEqual(len(pdf_hash), 64)  # SHA-256 hash length


class ReportEmailTest(TestCase):
    """Tests for report email sending."""

    def setUp(self):
        """Set up test data."""
        # Create users and profiles
        vet_user = User.objects.create_user(
            username="vet@test.com",
            email="vet@test.com",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=vet_user,
            first_name="Carlos",
            last_name="Rodríguez",
            license_number="MP-12345-REPORTS",
            email="vet@test.com",
        )

        histo_user = User.objects.create_user(
            username="histo@test.com",
            email="histo@test.com",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
        )
        self.histopathologist = Histopathologist.objects.create(
            user=histo_user,
            first_name="Ana",
            last_name="López",
            license_number="MV-54321",
            is_active=True,
        )

        # Create protocol
        self.protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            submission_date=date.today(),
            status=Protocol.Status.READY,
        )
        self.protocol.protocol_number = "HP 24/001"
        self.protocol.save()

        # Create finalized report with mock PDF
        self.report = Report.objects.create(
            protocol=self.protocol,
            histopathologist=self.histopathologist,
            veterinarian=self.veterinarian,
            diagnosis="Test diagnosis",
            status=Report.Status.FINALIZED,
            pdf_path="/tmp/test.pdf",
            pdf_hash="testhash123",
        )

    def test_report_send_view_requires_finalized_status(self):
        """Test that only finalized reports can be sent."""
        # Change status to draft
        self.report.status = Report.Status.DRAFT
        self.report.save()

        self.client.login(username="histo@test.com", password="testpass123")
        url = reverse("protocols:report_send", args=[self.report.pk])
        response = self.client.get(url)

        # Should redirect with error message
        self.assertEqual(response.status_code, 302)


class HistopathologistModelTest(TestCase):
    """Tests for Histopathologist model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="histo@test.com",
            email="histo@test.com",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
        )
        self.histopathologist = Histopathologist.objects.create(
            user=self.user,
            first_name="Ana",
            last_name="López",
            license_number="MV-54321",
            position="Profesora Asociada",
            specialty="Patología Veterinaria",
            is_active=True,
        )

    def test_histopathologist_creation(self):
        """Test histopathologist can be created."""
        self.assertEqual(self.histopathologist.user, self.user)
        self.assertEqual(self.histopathologist.license_number, "MV-54321")
        self.assertTrue(self.histopathologist.is_active)

    def test_histopathologist_get_full_name(self):
        """Test get_full_name method."""
        expected = "Ana López"
        self.assertEqual(self.histopathologist.get_full_name(), expected)

    def test_histopathologist_get_formal_name(self):
        """Test get_formal_name method."""
        expected = "Dr./Dra. Ana López"
        self.assertEqual(self.histopathologist.get_formal_name(), expected)

    def test_histopathologist_has_signature(self):
        """Test has_signature method."""
        self.assertFalse(self.histopathologist.has_signature())

    def test_histopathologist_str(self):
        """Test string representation."""
        expected = "Ana López"
        self.assertEqual(str(self.histopathologist), expected)
